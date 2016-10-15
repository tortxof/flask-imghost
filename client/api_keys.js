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

export default React.createClass({
  componentDidMount() {
    this.props.updateApiKeys()
  },
  render() {
    return (
      <div>
        <div>API Keys</div>
        {this.props.apiKeys.map(api_key => <ApiKey api_key={api_key} />)}
      </div>
    )
  }
})
