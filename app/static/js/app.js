"use strict";

function updateWitnessPreview(select) {
	const row = select.closest(".concept-row");
	const preview = row?.querySelector(".witness-preview");
	if (!preview) return;
	const paragraph = [...document.querySelectorAll(".paragraph-list [data-paragraph-id]")]
		.find((item) => item.dataset.paragraphId === select.value);
	const id = preview.querySelector("[data-witness-id]");
	const text = preview.querySelector("[data-witness-text]");
	if (id) id.textContent = select.value;
	if (text) text.textContent = paragraph?.querySelector("p")?.textContent ?? "";
}

document.querySelectorAll(".concept-row select[name='paragraph_ids']").forEach((select) => {
	select.addEventListener("change", () => updateWitnessPreview(select));
});

document.querySelectorAll("[data-add-concept]").forEach((button) => {
	button.addEventListener("click", () => {
		const template = document.querySelector("#concept-row-template");
		const rows = document.querySelector("#concept-rows");
		if (!template || !rows) return;
		document.querySelector("#no-concepts-row")?.remove();
		const row = template.content.cloneNode(true);
		rows.append(row);
		const select = rows.lastElementChild?.querySelector("select[name='paragraph_ids']");
		if (select) {
			select.addEventListener("change", () => updateWitnessPreview(select));
			updateWitnessPreview(select);
		}
	});
});

document.querySelectorAll("[data-copy]").forEach((button) => {
	button.addEventListener("click", async () => {
		const source = document.querySelector(button.dataset.copy);
		if (!source) return;
		try {
			await navigator.clipboard.writeText(source.value);
			const originalText = button.textContent;
			button.textContent = "کپی شد";
			window.setTimeout(() => { button.textContent = originalText; }, 1400);
		} catch {
			source.focus();
			source.select();
		}
	});
});

document.querySelectorAll("form[data-confirm]").forEach((form) => {
	form.addEventListener("submit", (event) => {
		if (!window.confirm(form.dataset.confirm)) event.preventDefault();
	});
});
