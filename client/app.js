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
              setUser: this.setUser
            }
          )
        }
      </div>
    )
  }
})
