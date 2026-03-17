function addPOLine() {
    const container = document.getElementById('po-lines');
    if (!container) return;

    const firstLine = container.querySelector('.po-line');
    if (!firstLine) return;

    const clone = firstLine.cloneNode(true);

    const heading = clone.querySelector('h3');
    const currentCount = container.querySelectorAll('.po-line').length + 1;
    if (heading) {
        heading.textContent = `Order Line ${currentCount}`;
    }

    clone.querySelectorAll('input').forEach(input => {
        input.value = '';
    });

    clone.querySelectorAll('select').forEach((select, index) => {
        if (select.options.length > 0) {
            select.selectedIndex = 0;
        }
    });

    container.appendChild(clone);
}
