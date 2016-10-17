import React from 'react'
import {Link} from 'react-router'

export default React.createClass({
  render() {
    return (
      <nav>
        <ul>
          <li><Link to='api-keys'>API Keys</Link></li>
          <li><Link to='collections'>Collections</Link></li>
          <li><Link to='images'>Images</Link></li>
          <li><Link to='create-account'>Create Account</Link></li>
          <li>{this.props.user ? <Link to='login'>Logged in as {this.props.user.username}</Link> : <Link to='login'>Log In</Link>}</li>
        </ul>
      </nav>
    )
  }
})
