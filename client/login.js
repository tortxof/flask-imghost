import React from 'react'

export default React.createClass({
  handleUsernameChange(e) {
    this.setState({
      username: e.target.value
    })
  },
  handlePasswordChange(e) {
    this.setState({
      password: e.target.value
    })
  },
  handleSubmit(e) {
    e.preventDefault()
    fetch('/api/session', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      method: 'POST',
      body: JSON.stringify({
        username: this.state.username,
        password: this.state.password
      })
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(session => {
          if (session.loggedIn) {
            this.props.setUser(session.user)
          }
        })
      }
    })
  },
  getInitialState() {
    return {username: '', password: ''}
  },
  render() {
    return (
      <div>
        <h2>Log In</h2>
        <form onSubmit={this.handleSubmit}>
          <input
            type='text'
            onChange={this.handleUsernameChange}
            value={this.state.username}
            placeholder='username'
            autoFocus
          />
          <input
            type='password'
            onChange={this.handlePasswordChange}
            value={this.state.password}
            placeholder='password'
          />
          <button type='submit'>Log In</button>
        </form>
        <a href='/logout'>Log Out</a>
      </div>
    )
  }
})
