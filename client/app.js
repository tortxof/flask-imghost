import React from 'react'

import Nav from './nav'

export default React.createClass({
  setUser(user) {
    this.setState({
      user: user
    })
  },
  getLoggedInUser() {
    fetch('/api/users', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(users => {
          if (users.length > 0) {
            this.setState({
              user: users[0]
            })
          }
        })
      }
    })
  },
  updateApiKeys() {
    fetch('/api/api-keys', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
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
  },
  updateCollections() {
    fetch('/api/collections', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(collections => {
          this.setState({
            collections: collections
          })
        })
      }
    })
  },
  componentDidMount() {
    this.getLoggedInUser()
  },
  getInitialState() {
    return {
      user: null,
      apiKeys: [],
      collections: [],
      images: [],
      currentCollection: null,
      currentImage: null
    }
  },
  render() {
    return (
      <div className='app-container'>
        <Nav user={this.state.user} />
        <div className='app-content'>
          {
            React.cloneElement(
              this.props.children,
              {
                setUser: this.setUser,
                updateApiKeys: this.updateApiKeys,
                updateCollections: this.updateCollections,
                apiKeys: this.state.apiKeys,
                collections: this.state.collections
              }
            )
          }
        </div>
      </div>
    )
  }
})
