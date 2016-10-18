import React from 'react'

const Collection = ({
  collection,
  handleDelete
}) => (
  <div className='collection'>
    <div>{collection.name}</div>
    <button data-uri={collection.uri} onClick={handleDelete}>&times;</button>
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
      fetch('/api/collections', {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
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
  handleDelete(e) {
    const uri = e.target.dataset.uri
    fetch(uri, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
      method: 'DELETE'
    })
    .then(response => {
      if (response.status >= 200 && response.status < 300) {
        this.props.updateCollections()
      }
    })
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
                handleDelete={this.handleDelete}
              />
            )
          )
        }
      </div>
    )
  }
})
