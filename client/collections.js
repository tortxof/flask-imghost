import React from 'react'

const Collection = ({
  collection
}) => (
  <div className='collection'>
    <div>{collection.name}</div>
  </div>
)

const NewCollectionForm = React.createClass({
  handleNameChange(e) {
    this.setState({
      name: e.target.value
    })
  },
  handleSubmit(e) {
    e.preventDefault()
    if (this.state.name.length > 0) {
      const auth_string = btoa(`:${this.props.apiKey.key}`)
      fetch('/api/collections', {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Basic ${auth_string}`
        },
        method: 'POST',
        body: JSON.stringify({name: this.state.name})
      })
      .then(response => {
        if (response.status >= 200 && response.status < 300) {
          this.props.updateCollections()
        }
      })
    }
  },
  getInitialState() {
    return {name: ''}
  },
  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <input
          type='text'
          onChange={this.handleNameChange}
          value={this.state.name}
          placeholder='collecton-name' />
        <button type='submit'>Create Collection</button>
      </form>
    )
  }
})

export default React.createClass({
  componentDidMount() {
    this.props.updateCollections()
  },
  render() {
    return (
      <div>
        <div>Collections</div>
        <NewCollectionForm
          apiKey={this.props.apiKey}
          updateCollections={this.props.updateCollections}
        />
        {
          this.props.collections.map(
            collection => (
              <Collection
                collection={collection}
                key={collection.name}
              />
            )
          )
        }
      </div>
    )
  }
})
