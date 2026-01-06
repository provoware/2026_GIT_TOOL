import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        console: "readonly",
        process: "readonly",
        __dirname: "readonly",
        __filename: "readonly",
        document: "readonly",
        window: "readonly",
        navigator: "readonly",
        crypto: "readonly",
        setInterval: "readonly"
      }
    },
    rules: {
      "no-console": "off"
    }
  }
];
