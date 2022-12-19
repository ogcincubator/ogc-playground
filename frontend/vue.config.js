const {defineConfig} = require('@vue/cli-service');
const CopyPlugin = require("copy-webpack-plugin");
module.exports = defineConfig({
    publicPath: 'auto',
    transpileDependencies: true,

    pluginOptions: {
        vuetify: {
            // https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vuetify-loader
        }
    },

    configureWebpack: {
        plugins: [
            new CopyPlugin({
                patterns: [{
                    from: "src/env-config.js",
                    to: "env-config.js",
                    transform(content) {
                        const envConf = Object.entries(process.env)
                            .filter(([key]) => key.startsWith('VUE_APP_'))
                            .reduce(
                                (acc, cur) =>
                                    `${acc}\n${cur[0].replace(/^VUE_APP_/, 'window.ogcPlayground.')}=${JSON.stringify(cur[1])};`, '');
                        return content.toString().replace('//OGC_PLAYGROUND_CONFIG', envConf);
                    },
                    info: { minimized: true },
                }],
            }),
        ],
    },
})
