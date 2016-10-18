import React from 'react'

const FileUpload =  ({
  filename,
  message,
  loaded,
  total
}) => {
  return (
    <div className='upload-progress'>
      <div className='filename'>{filename}</div>
      <div className='message'>{message}</div>
      <div className='status'>
        {
          loaded < total ?
          `${loaded} / ${total}` :
          total
        }
      </div>
      <progress value={loaded} max={total}></progress>
    </div>
  )
}


export default React.createClass({
  handleChange(e) {
    for (let i = 0; i < e.target.files.length; i++) {
      this.props.handleUpload(e.target.files[i])
    }
    e.target.value = ''
  },
  render() {
    const num_uploads = Object.keys(this.props.uploads).length
    const num_done = Object.keys(this.props.uploads).filter(key => this.props.uploads[key].state === 'done').length
    const num_wait = Object.keys(this.props.uploads).filter(key => this.props.uploads[key].state === 'wait').length
    const num_upload = Object.keys(this.props.uploads).filter(key => this.props.uploads[key].state === 'upload').length
    const num_thumb = Object.keys(this.props.uploads).filter(key => this.props.uploads[key].state === 'thumb').length
    const num_fail = Object.keys(this.props.uploads).filter(key => this.props.uploads[key].state === 'abort' || this.props.uploads[key].state === 'error').length
    const uploads = Object.keys(this.props.uploads).reverse().map(key => {
      return (
        <FileUpload
          key={key}
          filename={this.props.uploads[key].filename}
          message={this.props.uploads[key].message}
          loaded={this.props.uploads[key].loaded}
          total={this.props.uploads[key].total}
        />
      )
    })
    return (
      <div>
        <input type='file' name='file' onChange={this.handleChange} multiple />
        <div>Waiting: {num_wait}</div>
        <div>Uploading: {num_upload}</div>
        <div>Creating thumbnails: {num_thumb}</div>
        <div>Done: {num_done}</div>
        <div>Failed: {num_fail}</div>
        <div>Total: {num_uploads}</div>
        <div className='uploads'>
          {uploads}
        </div>
      </div>
    )
  }
})
