package com.testgen;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.File;
import java.io.FileNotFoundException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class AnalyzerCLI {

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: analyzer-cli <directory>");
            System.exit(1);
        }

        Path rootDir = Paths.get(args[0]);
        if (!Files.exists(rootDir) || !Files.isDirectory(rootDir)) {
            System.err.println("Directory not found: " + rootDir);
            System.exit(1);
        }

        JavaParser parser = new JavaParser();
        List<Map<String, Object>> fileResults = new ArrayList<>();
        int totalClasses = 0;
        int totalMethods = 0;

        try (Stream<Path> paths = Files.walk(rootDir)) {
            List<Path> javaFiles = paths
                    .filter(p -> p.toString().endsWith(".java"))
                    .collect(Collectors.toList());

            for (Path javaFile : javaFiles) {
                try {
                    ParseResult<CompilationUnit> result = parser.parse(javaFile);
                    if (!result.isSuccessful() || result.getResult().isEmpty()) {
                        System.err.println("Failed to parse: " + javaFile);
                        continue;
                    }

                    CompilationUnit cu = result.getResult().get();
                    List<Map<String, Object>> classes = extractClasses(cu, javaFile);
                    totalClasses += classes.size();
                    for (Map<String, Object> cls : classes) {
                        @SuppressWarnings("unchecked")
                        List<?> methods = (List<?>) cls.get("methods");
                        if (methods != null) totalMethods += methods.size();
                    }

                    Map<String, Object> fileMap = new LinkedHashMap<>();
                    fileMap.put("path", javaFile.toString());
                    fileMap.put("package", cu.getPackageDeclaration().map(pd -> pd.getName().asString()).orElse(""));
                    fileMap.put("classes", classes);
                    fileResults.add(fileMap);

                } catch (Exception e) {
                    System.err.println("Error processing " + javaFile + ": " + e.getMessage());
                }
            }
        }

        Map<String, Object> output = new LinkedHashMap<>();
        output.put("files", fileResults);
        output.put("total_classes", totalClasses);
        output.put("total_methods", totalMethods);

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        System.out.println(gson.toJson(output));
    }

    private static List<Map<String, Object>> extractClasses(CompilationUnit cu, Path filePath) {
        List<Map<String, Object>> classes = new ArrayList<>();

        for (TypeDeclaration<?> type : cu.getTypes()) {
            Map<String, Object> classMap = new LinkedHashMap<>();
            classMap.put("name", type.getNameAsString());
            classMap.put("annotations", type.getAnnotations().stream()
                    .map(a -> a.getNameAsString()).collect(Collectors.toList()));
            classMap.put("modifiers", type.getModifiers().stream()
                    .map(m -> m.getKeyword().asString()).collect(Collectors.toList()));

            if (type instanceof ClassOrInterfaceDeclaration) {
                ClassOrInterfaceDeclaration classDecl = (ClassOrInterfaceDeclaration) type;
                classMap.put("is_interface", classDecl.isInterface());
                classMap.put("extends", classDecl.getExtendedTypes().stream()
                        .map(t -> t.getNameAsString()).collect(Collectors.toList()));
                classMap.put("implements", classDecl.getImplementedTypes().stream()
                        .map(t -> t.getNameAsString()).collect(Collectors.toList()));
            } else {
                classMap.put("is_interface", false);
                classMap.put("extends", Collections.emptyList());
                classMap.put("implements", Collections.emptyList());
            }

            List<Map<String, Object>> methods = new ArrayList<>();
            for (MethodDeclaration method : type.getMethods()) {
                methods.add(extractMethod(method));
            }
            classMap.put("methods", methods);
            classes.add(classMap);
        }

        return classes;
    }

    private static Map<String, Object> extractMethod(MethodDeclaration method) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("name", method.getNameAsString());
        m.put("return_type", method.getType().asString());
        m.put("modifiers", method.getModifiers().stream()
                .map(mod -> mod.getKeyword().asString()).collect(Collectors.toList()));
        m.put("annotations", method.getAnnotations().stream()
                .map(a -> a.getNameAsString()).collect(Collectors.toList()));

        List<Map<String, String>> params = new ArrayList<>();
        for (com.github.javaparser.ast.body.Parameter p : method.getParameters()) {
            Map<String, String> param = new LinkedHashMap<>();
            param.put("name", p.getNameAsString());
            param.put("type", p.getType().asString());
            params.add(param);
        }
        m.put("parameters", params);

        String body = method.getBody().map(b -> b.toString()).orElse("");
        m.put("body", body);
        m.put("source", method.toString());
    

        // Control flow analysis
        int complexity = 1; // base
        boolean hasTryCatch = false;
        List<String> controlFlowKeywords = new ArrayList<>();

        if (method.getBody().isPresent()) {
            BlockStmt bodyStmt = method.getBody().get();

            // Count if statements
            long ifCount = bodyStmt.findAll(IfStmt.class).size();
            long forCount = bodyStmt.findAll(ForStmt.class).size();
            long foreachCount = bodyStmt.findAll(ForEachStmt.class).size();
            long whileCount = bodyStmt.findAll(WhileStmt.class).size();
            long doWhileCount = bodyStmt.findAll(DoStmt.class).size();
            long switchCount = bodyStmt.findAll(SwitchEntry.class).stream()
                    .filter(se -> !se.getLabels().isEmpty()).count();
            long catchCount = bodyStmt.findAll(CatchClause.class).size();
            long andCount = bodyStmt.findAll(BinaryExpr.class).stream()
                    .filter(b -> b.getOperator() == BinaryExpr.Operator.AND).count();
            long orCount = bodyStmt.findAll(BinaryExpr.class).stream()
                    .filter(b -> b.getOperator() == BinaryExpr.Operator.OR).count();

            complexity += ifCount + forCount + foreachCount + whileCount + doWhileCount + switchCount + catchCount + andCount + orCount;
            hasTryCatch = catchCount > 0;

            if (ifCount > 0) controlFlowKeywords.add("if");
            if (forCount > 0) controlFlowKeywords.add("for");
            if (foreachCount > 0) controlFlowKeywords.add("foreach");
            if (whileCount > 0) controlFlowKeywords.add("while");
            if (doWhileCount > 0) controlFlowKeywords.add("do-while");
            if (switchCount > 0) controlFlowKeywords.add("switch");
            if (hasTryCatch) controlFlowKeywords.add("try-catch");
        }

        m.put("has_try_catch", hasTryCatch);
        m.put("cyclomatic_complexity", complexity);
        m.put("control_flow_keywords", controlFlowKeywords);

        return m;
    }
}
