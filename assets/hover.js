document.addEventListener('mouseover', function (e) {
    const cardItem = e.target.closest('.card-row');
    if (cardItem) {
        const imgSrc = cardItem.getAttribute('data-image');
        const previewImg = document.getElementById('fixed-preview-img');
        if (previewImg && imgSrc) {
            previewImg.src = imgSrc;
            previewImg.style.display = 'block';
        }
    }
});