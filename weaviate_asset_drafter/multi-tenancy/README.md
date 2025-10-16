# multi-tenancy

Made with ❤️ and [Spectacle](https://github.com/FormidableLabs/spectacle/).

## Running your presentation

- Run `yarn install` (or `npm install` or `pnpm install`) to install dependencies.
- Run `yarn start` (or `npm start` or `pnpm start`) to start the presentation.
- Edit `slides.md` to add your presentation content.

You may need to run `yarn add --dev raw-loader` if you encounter issues with loading markdown files.

## Building you presentation

To build your presentation for a production deploy, run `yarn build` (or `npm build` or `pnpm build`).

The build artifacts will be placed in the `dist` directory. If you'd like to change this location, edit `output.path` in `webpack.config.js`.
