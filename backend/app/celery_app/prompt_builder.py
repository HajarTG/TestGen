"""
Step 4: Prompt Builder - assembles the final prompt and calls GPT-4o.

Combines:
  - Method source code
  - Class context
  - Selected strategy
  - RAG-retrieved similar code
into a carefully structured prompt, then calls the OpenAI Chat API.
"""
import logging
from typing import Dict, Any

from openai import OpenAI
from app.config import get_settings
from app.routers.metrics import GPT_CALLS, GPT_TOKENS

settings = get_settings()
logger = logging.getLogger(__name__)

# Cost per token (GPT-4o pricing as of 2024)
COST_PER_INPUT_TOKEN = 2.50 / 1_000_000   # $2.50 per 1M input tokens
COST_PER_OUTPUT_TOKEN = 10.00 / 1_000_000  # $10.00 per 1M output tokens

STRATEGY_INSTRUCTIONS = {
    "http_test": """Generate an integration test using Spring MockMvc or WebTestClient.
- Test HTTP endpoints (GET, POST, PUT, DELETE)
- Verify status codes, response bodies, and headers
- Use @WebMvcTest or @SpringBootTest
- Include tests for valid requests, invalid requests, and error responses""",

    "unit_mock_test": """Generate a unit test with Mockito for dependency mocking.
- Use @ExtendWith(MockitoExtension.class)
- Mock all injected dependencies with @Mock
- Use @InjectMocks for the class under test
- Verify method calls with verify() and argument matchers
- Test both success and failure paths
- IMPORTANT: If the method catches exceptions internally and returns null on failure,
  do NOT use assertThrows() — instead assertNull the return value and verify
  the correct notification/fallback method was called with verify()
- IMPORTANT: If the method returns a randomly generated ID (e.g. booking ID prefixed
  with "BK-"), do NOT assertEquals against a hardcoded ID — instead assertNotNull
  the return value and verify it starts with the expected prefix using
  assertTrue(result.startsWith("BK-"))
- IMPORTANT: Any test method that calls verify() or when() on a method that declares
  a checked exception MUST declare "throws <CheckedException>" in the test signature,
  even if the exception is never actually thrown in that test
- IMPORTANT: NEVER use when(...).thenReturn() or when(...).thenAnswer() on void methods —
  void methods cannot be stubbed with when(). To stub a void method use
  doNothing().when(mock).method() or simply do nothing (void methods do nothing by default).
  To stub a void method to throw, use doThrow().when(mock).method()""",


    "exception_test": """Generate tests focused on exception handling and error paths.
- Test every catch block and exception type
- Use assertThrows() ONLY for exceptions that actually propagate out of the method
- If the method catches exceptions internally and returns null, use assertNull() instead
- Verify exception messages
- Test boundary conditions that trigger exceptions
- Ensure proper error propagation""",

    "branch_coverage_test": """Generate comprehensive tests for all code branches.
- Test every if/else branch
- Test switch statement cases including default
- Test loop boundary conditions (0, 1, many)
- Use parameterized tests with @ParameterizedTest where applicable
- Aim for maximum branch coverage""",

    "data_access_test": """Generate a data access / repository integration test.
- Use @DataJpaTest or @SpringBootTest
- Test CRUD operations
- Verify query results
- Test with edge cases (empty results, null values)
- Use @Transactional for test isolation""",

    "unit_test": """Generate a standard unit test.
- Use JUnit 5 (@Test, @BeforeEach, @AfterEach)
- Test the primary success path
- Test edge cases and boundary values
- Include meaningful assertion messages
- Follow AAA pattern (Arrange, Act, Assert)""",
}


def _build_prompt(
    class_name: str,
    method: Dict[str, Any],
    strategy: str,
    rag_context: str,
    class_source: str,
) -> str:
    """Assemble the full GPT prompt."""
    method_source = method.get("source", "")
    method_name = method.get("name", "unknown")
    return_type = method.get("return_type", "void")
    params = method.get("parameters", "")

    strategy_instruction = STRATEGY_INSTRUCTIONS.get(strategy, STRATEGY_INSTRUCTIONS["unit_test"])

    prompt = f"""You are an expert Java test engineer. Generate a complete, compilable JUnit 5 test class for the following Java method.

## Method Under Test
Class: {class_name}
Method: {method_name}
Return type: {return_type}
Parameters: {params}

````java
{method_source}
````

## Full Class Context
````java
{class_source[:3000]}
````

## Testing Strategy
{strategy_instruction}

{f'''## Similar Code Reference (for context)
````java
{rag_context[:2000]}
```''' if rag_context else ''}

## Requirements
1. Generate a COMPLETE, COMPILABLE JUnit 5 test class
2. Include all necessary imports
3. Name the test class: {class_name}Test (or {class_name}{method_name.capitalize()}Test)
4. Use descriptive test method names following: test_methodName_scenario_expectedResult
5. Include at least 3 test methods covering different scenarios
6. Add meaningful assertion messages
7. Follow best practices (AAA pattern, single assertion per test when possible)
8. Do NOT include any explanation - return ONLY the Java test code
9. CRITICAL: Read the method body carefully — if exceptions are caught internally
   and the method returns null on failure, NEVER use assertThrows() for those cases;
   use assertNull() and verify() instead
10. CRITICAL: Never assertEquals a randomly generated ID — use assertNotNull() and
    assertTrue(result.startsWith("BK-")) or the relevant prefix instead
11. CRITICAL: For methods with multiple dependencies (repositories, gateways, services),
    always use @Mock and @InjectMocks — never instantiate the class directly
12. CRITICAL: When using verify(mock, never()).method() on methods that declare
    checked exceptions, the enclosing test method MUST be declared with
    "throws <CheckedException>" even if never() is used — javac still requires it.
    Example: void test_something() throws PaymentException {{ ... }}

## Output
Return ONLY the complete Java test file content, starting with package/import statements.
"""
    return prompt


def generate_test_for_method(
    class_name: str,
    method: Dict[str, Any],
    strategy: str,
    rag_context: str,
    class_source: str,
) -> Dict[str, Any]:
    """
    Build prompt and call GPT to generate a test.

    Returns dict with:
      - test_code: str
      - tokens_used: int
      - cost_usd: float
    """
    if not settings.effective_api_key or settings.effective_api_key == "sk-your-key-here":
        logger.warning("No LLM API key configured, generating placeholder test")
        return _placeholder_test(class_name, method)

    prompt = _build_prompt(class_name, method, strategy, rag_context, class_source)

    try:
        client = OpenAI(
            api_key=settings.effective_api_key,
            base_url=settings.effective_api_base
        )
        response = client.chat.completions.create(
            model=settings.effective_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Java test engineer. Output ONLY valid Java code, "
                        "no markdown fences, no explanations. "
                        "Before writing any test, carefully read the method body to understand "
                        "whether exceptions are thrown or caught internally, and whether return "
                        "values are fixed or randomly generated."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )

        test_code = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if test_code.startswith("```java"):
            test_code = test_code[7:]
        if test_code.startswith("```"):
            test_code = test_code[3:]
        if test_code.endswith("```"):
            test_code = test_code[:-3]
        test_code = test_code.strip()

        # Token usage
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = input_tokens + output_tokens
        cost = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)

        # Prometheus metrics
        GPT_CALLS.inc()
        GPT_TOKENS.labels(type="prompt").inc(input_tokens)
        GPT_TOKENS.labels(type="completion").inc(output_tokens)

        logger.info(f"Generated test for {class_name}.{method.get('name')} "
                     f"({total_tokens} tokens, ${cost:.4f})")

        return {
            "test_code": test_code,
            "tokens_used": total_tokens,
            "cost_usd": cost,
        }

    except Exception as e:
        logger.error(f"GPT call failed for {class_name}.{method.get('name')}: {e}")
        return _placeholder_test(class_name, method)


def _placeholder_test(class_name: str, method: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a placeholder test when GPT is unavailable."""
    method_name = method.get("name", "unknown")
    return {
        "test_code": f"""import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Auto-generated test for {class_name}.{method_name}
 * NOTE: This is a placeholder - configure OPENAI_API_KEY for AI-generated tests.
 */
class {class_name}Test {{

    private {class_name} underTest;

    @BeforeEach
    void setUp() {{
        // TODO: Initialize underTest with required dependencies
    }}

    @Test
    void test_{method_name}_success() {{
        // TODO: Implement test
        assertNotNull(underTest, "Instance should not be null");
    }}

    @Test
    void test_{method_name}_nullInput() {{
        // TODO: Test with null input
        assertThrows(IllegalArgumentException.class, () -> {{
            // underTest.{method_name}(null);
        }});
    }}

    @Test
    void test_{method_name}_edgeCase() {{
        // TODO: Test edge case
        assertTrue(true, "Edge case placeholder");
    }}
}}
""",
        "tokens_used": 0,
        "cost_usd": 0.0,
    }
