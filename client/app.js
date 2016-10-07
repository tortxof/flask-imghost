import React from 'react'

import Nav from './nav'

export default React.createClass({
  setApiKey(key) {
    this.setState({apiKey: key})
  },
  getInitialState() {
    return {
      apiKey: '',
      collections: [],
      images: [],
      currentCollection: '',
      currentImage: ''
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
              setApiKey: this.setApiKey
            }
          )
        }
      </div>
    )
  }
})
