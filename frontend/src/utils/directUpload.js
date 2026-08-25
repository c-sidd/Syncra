import api from './api';

const MULTIPART_THRESHOLD = 8 * 1024 * 1024;

const uploadPart = (url, blob, onProgress) => new Promise((resolve, reject) => {
  const xhr = new XMLHttpRequest();
  xhr.open('PUT', url);
  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) onProgress(event.loaded, event.total);
  };
  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const etag = xhr.getResponseHeader('ETag');
      if (!etag) return reject(new Error('S3 did not return an ETag for the uploaded part.'));
      resolve(etag);
    } else reject(new Error(`S3 part upload failed (${xhr.status}).`));
  };
  xhr.onerror = () => reject(new Error('Network error while uploading to S3.'));
  xhr.onabort = () => reject(new Error('Upload was cancelled.'));
  xhr.send(blob);
});

export async function directUpload(file, folderId = null, onProgress) {
  const report = onProgress || (() => {});

  if (file.size > MULTIPART_THRESHOLD) {
    const init = await api.post('/files/upload/multipart/initiate/', {
      name: file.name,
      size: file.size,
      content_type: file.type || 'application/octet-stream',
      folder: folderId,
    });
    const { upload_id: uploadId, object_key: objectKey, part_size: partSize, parts } = init.data;
    const completedParts = [];
    let completedBytes = 0;

    for (const part of parts) {
      const start = (part.part_number - 1) * partSize;
      const end = Math.min(start + partSize, file.size);
      const blob = file.slice(start, end);
      const etag = await uploadPart(part.url, blob, (loaded) => {
        report(Math.round(((completedBytes + loaded) / file.size) * 100));
      });
      completedParts.push({ PartNumber: part.part_number, ETag: etag });
      completedBytes += blob.size;
      report(Math.round((completedBytes / file.size) * 100));
    }

    const complete = await api.post('/files/upload/multipart/complete/', {
      object_key: objectKey,
      upload_id: uploadId,
      parts: completedParts,
      name: file.name,
      folder: folderId,
    });
    return complete.data;
  }

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
      if (event.lengthComputable) report(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`S3 upload failed (${xhr.status}).`)));
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
