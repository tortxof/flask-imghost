import React from 'react'

const ApiKey = ({
  api_key,
  handleDelete
}) => (
  <div className='api-key'>
    <div className='key'>{api_key.key}</div>
    <div className='description'>{api_key.description}</div>
    <div className='date'>{api_key.date_created}</div>
    <button data-uri={api_key.uri} onClick={handleDelete}>&times;</button>
  </div>
)

const NewApiKeyForm = React.createClass({
  handleDescriptionChange(e) {
    this.setState({
      description: e.target.value
    })
  },
  handleSubmit(e) {
    e.preventDefault()
    fetch('/api/api-keys', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
      method: 'POST',
      body: JSON.stringify({description: this.state.description})
    })
    .then(response => {
      if (response.status >= 200 && response.status < 300) {
        this.props.updateApiKeys()
      }
    })
  },
  getInitialState() {
    return {description: ''}
  },
  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <input
          type='text'
          onChange={this.handleDescriptionChange}
          value={this.state.description}
          placeholder='API key description'
        />
        <button type='submit'>Create API Key</button>
      </form>
    )
  }
})

export default React.createClass({
  componentDidMount() {
    this.props.updateApiKeys()
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
        this.props.updateApiKeys()
      }
    })
  },
  render() {
    return (
      <div>
        <div>API Keys</div>
        <NewApiKeyForm
          apiKey={this.props.apiKey}
          updateApiKeys={this.props.updateApiKeys}
        />
        {
          this.props.apiKeys.map(
            api_key => (
              <ApiKey
                handleDelete={this.handleDelete}
                api_key={api_key}
                key={api_key.key}
              />
            )
          )
        }
      </div>
    )
  }
})
