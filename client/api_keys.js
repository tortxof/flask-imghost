import React from 'react'

const ApiKey = ({
  api_key
}) => (
  <div className='api-key'>
    <div>{api_key.key}</div>
    <div>{api_key.description}</div>
    <div>{api_key.date_created}</div>
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
    const auth_string = btoa(`:${this.props.apiKey.key}`)
    fetch('/api/api-keys', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth_string}`
      },
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
            api_key => <ApiKey api_key={api_key} key={api_key.key} />
          )
        }
      </div>
    )
  }
})
