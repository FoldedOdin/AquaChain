/**
 * CRACO Configuration for Webpack Customization
 * Optimizes asset loading and bundle splitting
 */

const ImageMinimizerPlugin = require('image-minimizer-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Only apply optimizations in production
      if (env === 'production') {
        // Configure code splitting for vendor bundles
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              // Vendor bundle for node_modules
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                priority: 10,
                reuseExistingChunk: true,
              },
              // React and related libraries
              react: {
                test: /[\\/]node_modules[\\/](react|react-dom|react-router-dom)[\\/]/,
                name: 'react-vendor',
                priority: 20,
                reuseExistingChunk: true,
              },
              // AWS and Amplify libraries
              aws: {
                test: /[\\/]node_modules[\\/](@aws-sdk|aws-amplify|@aws-amplify)[\\/]/,
                name: 'aws-vendor',
                priority: 20,
                reuseExistingChunk: true,
              },
              // Chart libraries
              charts: {
                test: /[\\/]node_modules[\\/](recharts|d3)[\\/]/,
                name: 'charts-vendor',
                priority: 15,
                reuseExistingChunk: true,
              },
              // Common code shared between chunks
              common: {
                minChunks: 2,
                priority: 5,
                reuseExistingChunk: true,
                enforce: true,
              },
            },
          },
          // Runtime chunk for webpack runtime code
          runtimeChunk: {
            name: 'runtime',
          },
        };

        // Add image optimization
        webpackConfig.plugins.push(
          new ImageMinimizerPlugin({
            minimizer: {
              implementation: ImageMinimizerPlugin.imageminMinify,
              options: {
                plugins: [
                  ['imagemin-mozjpeg', { quality: 75, progressive: true }],
                  ['imagemin-pngquant', { quality: [0.65, 0.90], speed: 4 }],
                  ['imagemin-svgo', {
                    plugins: [
                      {
                        name: 'preset-default',
                        params: {
                          overrides: {
                            removeViewBox: false,
                            addAttributesToSVGElement: {
                              params: {
                                attributes: [
                                  { xmlns: 'http://www.w3.org/2000/svg' },
                                ],
                              },
                            },
                          },
                        },
                      },
                    ],
                  }],
                ],
              },
            },
            generator: [
              {
                // Convert images to WebP
                preset: 'webp',
                implementation: ImageMinimizerPlugin.imageminGenerate,
                options: {
                  plugins: ['imagemin-webp'],
                },
              },
            ],
          })
        );

        // Add bundle analyzer in analyze mode
        if (process.env.ANALYZE) {
          webpackConfig.plugins.push(
            new BundleAnalyzerPlugin({
              analyzerMode: 'static',
              reportFilename: 'bundle-report.html',
              openAnalyzer: true,
            })
          );
        }
      }

      // Configure module rules for images
      const imageRule = webpackConfig.module.rules.find(rule => {
        return rule.test && rule.test.toString().includes('png|jpg|jpeg|gif');
      });

      if (imageRule) {
        imageRule.type = 'asset';
        imageRule.parser = {
          dataUrlCondition: {
            maxSize: 8 * 1024, // 8kb - inline images smaller than this
          },
        };
      }

      return webpackConfig;
    },
  },
  // DevServer configuration to fix deprecation warnings
  devServer: {
    setupMiddlewares: (middlewares, devServer) => {
      // This replaces the deprecated onBeforeSetupMiddleware and onAfterSetupMiddleware
      if (!devServer) {
        throw new Error('webpack-dev-server is not defined');
      }

      // Custom middleware can be added here
      // middlewares.unshift(...);
      // middlewares.push(...);

      return middlewares;
    },
  },
  // Babel configuration for optimal transpilation
  babel: {
    plugins: [
      // Remove console logs in production
      ...(process.env.NODE_ENV === 'production'
        ? [['transform-remove-console', { exclude: ['error', 'warn'] }]]
        : []),
    ],
  },
};
