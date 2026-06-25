"""
Step 2: Strategy Selector - rule-based engine to choose test generation strategy.

Analyzes class/method annotations and code patterns to select the optimal
testing strategy for each method.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Strategy definitions
STRATEGIES = {
    "http_test": "Generate HTTP/integration test with MockMvc or WebTestClient",
    "unit_mock_test": "Generate unit test with Mockito mocks for dependencies",
    "exception_test": "Generate tests focusing on exception paths and error handling",
    "branch_coverage_test": "Generate tests for high-complexity methods covering all branches",
    "data_access_test": "Generate repository/data access layer test",
    "unit_test": "Generate standard unit test with assertions",
}

# Class-level annotation -> strategy mapping
CLASS_ANNOTATION_RULES = {
    "Controller": "http_test",
    "RestController": "http_test",
    "RequestMapping": "http_test",
    "Repository": "data_access_test",
    "JpaRepository": "data_access_test",
}

# Method-level annotation -> strategy mapping
METHOD_ANNOTATION_RULES = {
    "GetMapping": "http_test",
    "PostMapping": "http_test",
    "PutMapping": "http_test",
    "DeleteMapping": "http_test",
    "PatchMapping": "http_test",
    "RequestMapping": "http_test",
    "Transactional": "data_access_test",
    "Query": "data_access_test",
}

# Keywords that indicate injected dependencies requiring mocking
DEPENDENCY_KEYWORDS = [
    "Repository", "Service", "Gateway", "Client", "Mapper",
    "userRepository", "paymentGateway", "notificationService",
    "availabilityRepository", "@Autowired", "@Inject",
]

# Complexity threshold for branch coverage strategy
COMPLEXITY_THRESHOLD = 4


def _has_dependencies(source: str) -> bool:
    """Check if method source uses injected dependencies."""
    return any(keyword in source for keyword in DEPENDENCY_KEYWORDS)


def _select_strategy_for_method(
    class_annotations: list,
    method: Dict[str, Any],
) -> str:
    """Select the best strategy for a single method."""
    method_annotations = method.get("annotations", [])
    has_try_catch = method.get("has_try_catch", False)
    complexity = method.get("cyclomatic_complexity", 1)
    source = method.get("source", "")

    # Priority 1: Class-level annotations (controller, repository)
    for ann in class_annotations:
        if ann in CLASS_ANNOTATION_RULES:
            return CLASS_ANNOTATION_RULES[ann]

    # Priority 2: Method-level annotations
    for ann in method_annotations:
        if ann in METHOD_ANNOTATION_RULES:
            return METHOD_ANNOTATION_RULES[ann]

    # Priority 3: High complexity — but if dependencies exist, mocking matters more
    if complexity > COMPLEXITY_THRESHOLD:
        if _has_dependencies(source):
            return "unit_mock_test"
        return "branch_coverage_test"

    # Priority 4: Try/catch — but if dependencies exist, mocking matters more
    if has_try_catch:
        if _has_dependencies(source):
            return "unit_mock_test"
        return "exception_test"

    # Priority 5: Injected dependencies (suggests mocking needed)
    if _has_dependencies(source):
        return "unit_mock_test"

    # Default
    return "unit_test"


def select_strategies(code_model: Dict[str, Any]) -> Dict[str, str]:
    """
    Select strategies for all methods in the code model.

    Returns: dict mapping "ClassName.methodName" -> strategy name
    """
    strategies = {}

    for cls in code_model.get("classes", []):
        class_name = cls.get("name", "Unknown")
        class_annotations = cls.get("annotations", [])

        for method in cls.get("methods", []):
            method_name = method.get("name", "unknown")
            key = f"{class_name}.{method_name}"

            strategy = _select_strategy_for_method(class_annotations, method)
            strategies[key] = strategy
            logger.info(f"Strategy for {key}: {strategy}")

    return strategies