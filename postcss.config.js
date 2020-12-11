const path = require("path");
const autoprefixer = require("autoprefixer");
const tailwindcss = require("tailwindcss");
const purgecss = require("@fullhuman/postcss-purgecss");

module.exports = (ctx) => {
  const plugins = [
    require("tailwindcss")(path.resolve(__dirname, "tailwind.config.js")),
    require("autoprefixer"),
  ];

  if (ctx.env === "production") {
    plugins.push(
      require("@fullhuman/postcss-purgecss")({
        content: [path.resolve(__dirname, "templates/**/*.html")],
        defaultExtractor: (content) => content.match(/[A-Za-z0-9-_:/]+/g) || [],
      })
    );
  }

  return { plugins };
};
