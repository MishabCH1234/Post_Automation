module.exports = {
  content: [
    "../templates/**/*.html",
    "../../templates/**/*.html",
    "../../**/templates/**/*.html",
],

  plugins: {
    "@tailwindcss/postcss": {},
    "postcss-simple-vars": {},
    "postcss-nested": {}
  },
}


