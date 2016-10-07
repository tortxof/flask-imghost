const path = require('path')
const webpack = require('webpack')

module.exports = {
  entry: ['babel-polyfill', 'whatwg-fetch', './client/main.js'],
  output: {
    path: path.resolve(__dirname, 'static'),
    publicPath: '/static/',
    filename: 'bundle.js'
  },
  module: {
    loaders: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      }
    ]
  },
  plugins: [
    new webpack.DefinePlugin(
      {
        "process.env": {NODE_ENV: JSON.stringify(process.env.NODE_ENV)}
      }
    )
  ]
}
