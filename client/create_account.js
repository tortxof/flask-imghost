import React from 'react'
import {browserHistory} from 'react-router'

export default React.createClass({
  handleUsernameChange(e) {
    this.setState({
      username: e.target.value
    })
  },
  handleEmailChange(e) {
    this.setState({
      email: e.target.value
    })
  },
  handlePasswordChange(e) {
    this.setState({
      password: e.target.value
    })
  },
  handleSubmit(e) {
    e.preventDefault()
    fetch('/api/users', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: this.state.username,
        email: this.state.email,
        password: this.state.password
      })
    })
    .then(response => {
      if (response.status !== 200) {
        response.json().then(json => {
          this.setState({
            message: json.message
          })
        })
      } else {
        browserHistory.push('/login')
      }
    })

  },
  getInitialState() {
    return {username: '', email: '', password: '', message: ''}
  },
  render() {
    return (
      <div>
        <h2>Create Account</h2>
        <form onSubmit={this.handleSubmit}>
          <input
            type='text'
            onChange={this.handleUsernameChange}
            value={this.state.username}
            placeholder='username'
          />
          <input
            type='email'
            onChange={this.handleEmailChange}
            value={this.state.email}
            placeholder='email'
          />
          <input
            type='password'
            onChange={this.handlePasswordChange}
            value={this.state.password}
            placeholder='password'
          />
          <button >Create Account</button>
        </form>
        <div>{this.state.message}</div>
      </div>
    )
  }
})
