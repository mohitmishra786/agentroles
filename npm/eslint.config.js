export default [
  {
    files: ["bin/**/*.js"],
    rules: {
      "no-undef": "error",
      "no-unused-vars": "warn",
      "no-console": "off",
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: {
        process: "readonly",
        console: "readonly",
        __dirname: "readonly",
        require: "readonly",
        module: "readonly",
      },
    },
  },
];
