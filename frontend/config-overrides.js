module.exports = {
    webpack: {
      configure: {
        module: {
          rules: [
            {
              test: /plotly\.js/,
              use: {
                loader: 'source-map-loader',
                options: {
                  filterSourceMappingUrl: (url, resourcePath) => {
                    return false; // Disable source maps for plotly
                  }
                }
              }
            }
          ]
        }
      }
    }
  };