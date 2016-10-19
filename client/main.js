import React from 'react'
import ReactDOM from 'react-dom'
import {Router, Route, Link, IndexRoute, browserHistory} from 'react-router'

import App from './app'
import Home from './home'
import ApiKeys from './api_keys'
import Collections from './collections'
import CollectionDetail from './collection_detail'
import Images from './images'
import Upload from './upload'
import Login from './login'
import CreateAccount from './create_account'

ReactDOM.render(
  (
    <Router history={browserHistory}>
      <Route path='/' component={App}>
        <IndexRoute component={Home} />
        <Route path='api-keys' component={ApiKeys} />
        <Route path='collections' component={Collections} />
        <Route path='collections/:name' component={CollectionDetail} />
        <Route path='images' component={Images} />
        <Route path='upload' component={Upload} />
        <Route path='create-account' component={CreateAccount} />
        <Route path='login' component={Login} />
      </Route>
    </Router>
  ),
  document.getElementById('app')
)
