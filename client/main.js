import React from 'react'
import ReactDOM from 'react-dom'
import {Router, Route, Link, IndexRedirect, hashHistory} from 'react-router'

import App from './app'
import ApiKeys from './api_keys'
import Collections from './collections'
import Images from './images'

ReactDOM.render(
  (
    <Router history={hashHistory}>
      <Route path='/' component={App}>
        <Route path='api-keys' component={ApiKeys} />
        <Route path='collections' component={Collections} />
        <Route path='images' component={Images} />
      </Route>
    </Router>
  ),
  document.getElementById('app')
)
