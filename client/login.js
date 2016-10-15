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
      }
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(json => {
          this.props.setUser(json[0])
        })
        fetch('/api/api-keys', {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `Basic ${auth_string}`
          }
        })
        .then(response => {
          if (response.status === 200) {
            response.json().then(api_keys => {
              if (api_keys.length > 0) {
                this.props.setApiKey(api_keys[0])
              } else {
                fetch('/api/api-keys', {
                  method: 'POST',
                  headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': `Basic ${auth_string}`
                  },
                  body: JSON.stringify({
                    description: 'Automatically generated API key.'
                  })
                })
                .then(response => {
                  if (response.status >= 200 && response.status < 300) {
                    response.json().then(api_key => {
                      this.props.setApiKey(api_key)
                    })
                  }
                })
              }
            })
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
          />
          <input
            type='password'
            onChange={this.handlePasswordChange}
            value={this.state.password}
            placeholder='password'
          />
          <button type='submit'>Log In</button>
        </form>
      </div>
    )
  }
})
