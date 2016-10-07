import React from 'react'

export default React.createClass({
  handleSubmit() {
    console.log('handleSubmit');
  },
  render() {
    return (
      <div>
        <h2>Log In</h2>
        <form onSubmit={this.handleSubmit}>
          <input/>
          <input/>
          <button type='submit'>Log In</button>
        </form>
      </div>
    )
  }
})
