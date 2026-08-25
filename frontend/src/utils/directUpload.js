import api from './api';

/**
 * Upload a File directly to the user's S3 bucket through a short-lived
 * presigned PUT URL, keeping file bytes out of the Django process.
 */
export async function directUpload(file, folderId = null, onProgress) {
  const presign = await api.post('/files/upload/presign/', {
    name: file.name,
    size: file.size,
    content_type: file.type || 'application/octet-stream',
    folder: folderId,
  });

  const { upload_url: uploadUrl, object_key: objectKey } = presign.data;

  await new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', uploadUrl);
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`S3 upload failed (${xhr.status}).`));
    };
    xhr.onerror = () => reject(new Error('Network error while uploading to S3.'));
    xhr.onabort = () => reject(new Error('Upload was cancelled.'));
    xhr.send(file);
  });

  const complete = await api.post('/files/upload/complete/', {
    object_key: objectKey,
    name: presign.data.name,
    folder: folderId,
  });

  return complete.data;
}
