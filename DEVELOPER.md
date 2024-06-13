# Developer instructions

- Installing developer dependencies: `npm install`
- Running the unit tests: `npm test`
- Running eslint: `eslint index.js`

## Coding standards

If you plan to add or modify code, please follow these development guidelines:

- Minimize the use of asynchronous code. It can make the codebase harder to read and reason about.
- Declare all inputs as function parameters.
- Ensure functions are as free of side effects as possible.
- Write meaningful unit tests, and avoid unit testing standard libraries.