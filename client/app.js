import React from 'react'

import Nav from './nav'

export default React.createClass({
  setApiKey(key) {
    this.setState({apiKey: key})
  },
  setUser(user) {
    this.setState({
      user: user
    })
  },
  updateApiKeys() {
    if (this.state.apiKey) {
      const auth_string = btoa(`:${this.state.apiKey.key}`)
      fetch('/api/api-keys', {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Basic ${auth_string}`
        }
      })
      .then(response => {
        if (response.status === 200) {
          response.json().then(apiKeys => {
            this.setState({
              apiKeys: apiKeys
            })
          })
        }
      })
    }
  },
  getInitialState() {
    return {
      user: null,
      apiKey: null,
      apiKeys: [],
      collections: [],
      images: [],
      currentCollection: null,
      currentImage: null
    }
  },
  render() {
    return (
      <div>
        <Nav />
        {
          React.cloneElement(
            this.props.children,
            {
              setApiKey: this.setApiKey,
              setUser: this.setUser,
              updateApiKeys: this.updateApiKeys,
              apiKeys: this.state.apiKeys
            }
          )
        }
      </div>
    )
  }
})
