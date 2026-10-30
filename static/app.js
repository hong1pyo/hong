const file = document.querySelector('#file');
const drop = document.querySelector('#dropzone');
const preview = document.querySelector('#preview');
const placeholder = document.querySelector('#placeholder');
const analyze = document.querySelector('#analyze');
const error = document.querySelector('#error');
const result = document.querySelector('#result');

document.querySelector('#select').onclick = (event) => { event.stopPropagation(); file.click(); };
drop.onclick = () => file.click();

file.onchange = () => {
  const selected = file.files[0];
  if (!selected) return;
  error.hidden = true;
  if (selected.size > 10 * 1024 * 1024) {
    error.textContent = '10MB 이하 이미지만 업로드할 수 있어요.';
    error.hidden = false;
    analyze.disabled = true;
    return;
  }
  preview.src = URL.createObjectURL(selected);
  preview.hidden = false;
  placeholder.hidden = true;
  analyze.disabled = false;
  result.hidden = true;
};

analyze.onclick = async () => {
  const selected = file.files[0];
  if (!selected) return;
  analyze.disabled = true;
  analyze.textContent = '분석 중...';
  error.hidden = true;
  try {
    // No <form> element is needed: append the selected file explicitly.
    const formData = new FormData();
    formData.append('file', selected);
    const response = await fetch('/api/analyze', { method: 'POST', body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '분석에 실패했어요.');
    document.querySelector('#winner').textContent = data.winner;
    document.querySelector('#bars').innerHTML = Object.entries(data.results)
      .sort((a, b) => b[1] - a[1])
      .map(([name, percent]) => `<div class="bar"><div class="label"><span>${name}</span><b>${percent}%</b></div><div class="track"><div class="fill" style="width:${percent}%"></div></div></div>`).join('');
    result.hidden = false;
  } catch (exception) {
    error.textContent = exception.message;
    error.hidden = false;
  } finally {
    analyze.disabled = false;
    analyze.innerHTML = '동물상 분석하기 <span>→</span>';
  }
};

document.querySelector('#again').onclick = () => {
  file.value = '';
  preview.hidden = true;
  placeholder.hidden = false;
  result.hidden = true;
  analyze.disabled = true;
};

fetch('/api/status').then((response) => response.json()).then((status) => {
  document.querySelector('#status').textContent = status.model_ready
    ? 'CPU에서 실행되는 가벼운 MobileNetV2 모델' : '모델 준비가 필요합니다';
}).catch(() => {});
