(function () {
  var form = document.getElementById('rr-upload-form');
  var input = document.getElementById('rr-file-input');
  var dropZone = document.getElementById('rr-drop-zone');
  var list = document.getElementById('rr-upload-list');
  var summary = document.getElementById('rr-upload-summary');

  if (!form || !input || !dropZone || !list) {
    return;
  }

  function getCsrfToken() {
    var tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return tokenInput ? tokenInput.value : '';
  }

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    var units = ['B', 'KB', 'MB', 'GB'];
    var index = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, index)).toFixed(index ? 1 : 0) + ' ' + units[index];
  }

  function createRow(file) {
    var row = document.createElement('div');
    row.className = 'rr-upload-row';
    row.innerHTML = [
      '<div class="rr-upload-row-header"><strong></strong><span></span></div>',
      '<div class="rr-upload-bar"><span></span></div>',
      '<div class="rr-upload-status">Waiting</div>'
    ].join('');
    row.querySelector('strong').textContent = file.name;
    row.querySelector('.rr-upload-row-header span').textContent = formatBytes(file.size);
    list.appendChild(row);
    return row;
  }

  function setFiles(files) {
    input.files = files;
    renderSelectedFiles(Array.prototype.slice.call(files));
  }

  function renderSelectedFiles(files) {
    list.innerHTML = '';
    files.forEach(createRow);
    if (summary) {
      summary.textContent = files.length ? files.length + ' PDF file(s) selected' : '';
    }
  }

  function uploadFile(file, row, done) {
    var data = new FormData();
    data.append('csrfmiddlewaretoken', getCsrfToken());
    data.append('files', file);

    var xhr = new XMLHttpRequest();
    var bar = row.querySelector('.rr-upload-bar span');
    var status = row.querySelector('.rr-upload-status');
    var startedAt = Date.now();

    xhr.upload.addEventListener('progress', function (event) {
      if (!event.lengthComputable) return;
      var percent = Math.round((event.loaded / event.total) * 100);
      var elapsedSeconds = Math.max((Date.now() - startedAt) / 1000, 0.1);
      var speed = event.loaded / elapsedSeconds;
      bar.style.width = percent + '%';
      status.textContent = percent + '% • ' + formatBytes(speed) + '/s';
    });

    xhr.addEventListener('load', function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        row.classList.add('is-complete');
        bar.style.width = '100%';
        status.textContent = 'Upload complete';
      } else {
        row.classList.add('is-error');
        bar.style.width = '100%';
        status.textContent = 'Upload failed: ' + xhr.status;
      }
      done();
    });

    xhr.addEventListener('error', function () {
      row.classList.add('is-error');
      status.textContent = 'Upload failed: network error';
      done();
    });

    xhr.open('POST', form.action);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.send(data);
  }

  function uploadFiles(files) {
    var rows = Array.prototype.slice.call(list.querySelectorAll('.rr-upload-row'));
    var queue = Array.prototype.slice.call(files);
    var completed = 0;

    if (!queue.length) return;
    if (summary) summary.textContent = 'Uploading ' + queue.length + ' file(s)...';

    function next() {
      var file = queue.shift();
      var row = rows[completed];
      if (!file || !row) {
        if (summary) summary.textContent = 'Upload finished. Refreshing...';
        window.setTimeout(function () { window.location.reload(); }, 900);
        return;
      }
      uploadFile(file, row, function () {
        completed += 1;
        next();
      });
    }

    next();
  }

  ['dragenter', 'dragover'].forEach(function (name) {
    dropZone.addEventListener(name, function (event) {
      event.preventDefault();
      dropZone.classList.add('is-dragover');
    });
  });

  ['dragleave', 'drop'].forEach(function (name) {
    dropZone.addEventListener(name, function (event) {
      event.preventDefault();
      dropZone.classList.remove('is-dragover');
    });
  });

  dropZone.addEventListener('drop', function (event) {
    if (event.dataTransfer && event.dataTransfer.files) {
      setFiles(event.dataTransfer.files);
    }
  });

  input.addEventListener('change', function () {
    renderSelectedFiles(Array.prototype.slice.call(input.files));
  });

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var files = Array.prototype.slice.call(input.files).filter(function (file) {
      return file.name.toLowerCase().endsWith('.pdf');
    });
    if (!files.length) {
      if (summary) summary.textContent = 'Please select at least one PDF file.';
      return;
    }
    list.innerHTML = '';
    files.forEach(createRow);
    uploadFiles(files);
  });
})();
