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
    const auth_string = btoa(`${this.state.username}:${this.state.password}`)
    fetch('/api/users', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth_string}`
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(users => {
          this.props.setUser(users[0])
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
