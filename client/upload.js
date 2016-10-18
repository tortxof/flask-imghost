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
        <div className='uploads'>
          {uploads}
        </div>
      </div>
    )
  }
})
