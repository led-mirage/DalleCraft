function imageSizeGreatestCommonDivisor(a, b) {
    while (b !== 0) {
        [a, b] = [b, a % b];
    }
    return a;
}

function formatImageSizeLabel(size) {
    if (size === "auto") {
        return "自動";
    }

    const match = /^(\d+)x(\d+)$/.exec(size);
    if (!match) {
        return size;
    }

    const width = Number(match[1]);
    const height = Number(match[2]);
    if (width === height) {
        return `${width} × ${height}（正方形）`;
    }

    const divisor = imageSizeGreatestCommonDivisor(width, height);
    const ratio = `${width / divisor}:${height / divisor}`;
    const orientation = width > height ? "横長" : "縦長";
    return `${width} × ${height}（${orientation} ${ratio}）`;
}

function populateImageSizeSelect(select, presets, selectedSize) {
    select.replaceChildren();
    presets.forEach(size => {
        const option = document.createElement("option");
        option.value = size;
        option.textContent = formatImageSizeLabel(size);
        select.appendChild(option);
    });
    select.value = presets.includes(selectedSize) ? selectedSize : presets[0];
}

function populateImageSizeRadios(container, presets, selectedSize) {
    container.replaceChildren();
    const checkedSize = presets.includes(selectedSize) ? selectedSize : presets[0];

    presets.forEach((size, index) => {
        const item = document.createElement("div");
        item.className = "image-size-option";

        const radio = document.createElement("input");
        radio.type = "radio";
        radio.id = `optionImageSize${index}`;
        radio.name = "imageSize";
        radio.value = size;
        radio.checked = size === checkedSize;

        const label = document.createElement("label");
        label.htmlFor = radio.id;
        label.textContent = formatImageSizeLabel(size);

        item.append(radio, label);
        container.appendChild(item);
    });
}
