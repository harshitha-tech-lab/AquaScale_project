document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadSection = document.getElementById('uploadSection');
    const loadingState = document.getElementById('loadingState');

    // Wizard Screens
    const stepClassification = document.getElementById('stepClassification');
    const stepLength = document.getElementById('stepLength');
    const stepWeightPhase = document.getElementById('stepWeightPhase');

    // UI Elements
    const displayOriginal = document.getElementById('displayOriginal');
    const displayProcessed = document.getElementById('displayProcessed');
    const lengthOriginal = document.getElementById('lengthOriginal');

    // Results
    const resSpecies = document.getElementById('resSpecies');
    const lengthSpecies = document.getElementById('lengthSpecies');
    const finalSpecies = document.getElementById('finalSpecies');
    const resLength = document.getElementById('resLength');
    const finalLength = document.getElementById('finalLength');
    const resWeight = document.getElementById('resWeight');
    const resPhase = document.getElementById('resPhase');

    const btnMeasure = document.getElementById('btnMeasure');
    const btnProceedWeight = document.getElementById('btnProceedWeight');

    let currentFilename = null;
    let currentSpecies = null;

    // Drag & Drop
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    async function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file.');
            return;
        }

        // Show Loading
        uploadSection.classList.add('hidden');
        loadingState.classList.remove('hidden');

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Analysis failed');

            // Success - Stage 1
            currentFilename = data.filename;
            currentSpecies = data.species;

            // Update UI for Stage 1
            displayOriginal.src = data.image_url;
            resSpecies.textContent = data.species;

            loadingState.classList.add('hidden');
            stepClassification.classList.remove('hidden'); // Show Wizard Step 1

            // Ensure the measure button is active
            btnMeasure.disabled = false;
            btnMeasure.innerHTML = 'Proceed to Length Estimation <i class="fa-solid fa-arrow-right" style="margin-left: 0.5rem;"></i>';

        } catch (error) {
            console.error(error);
            alert(error.message);
            loadingState.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
    }

    // Stage 2: Measure
    btnMeasure.addEventListener('click', async () => {
        if (!currentFilename || !currentSpecies) return;

        btnMeasure.disabled = true;
        btnMeasure.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Estimating Growth...';

        // Wizard Transition: Hide Step 1, Show Loading for Step 2
        stepClassification.classList.add('hidden');
        loadingState.querySelector('h3').textContent = 'Estimating Length...';
        loadingState.querySelector('p').textContent = 'Generating full report';
        loadingState.classList.remove('hidden');

        try {
            const response = await fetch('/calculate_length', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: currentFilename,
                    species: currentSpecies
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Measurement failed');

            // Success - Stage 2
            if (lengthOriginal) lengthOriginal.src = displayOriginal.src; // Show original image in length view
            if (lengthSpecies) lengthSpecies.textContent = currentSpecies; // Show species in length view
            if (displayProcessed) displayProcessed.src = data.processed_image_url;
            if (resLength) resLength.textContent = `${data.length.toFixed(2)} cm`;

            // Prepare Step 3 items
            if (finalSpecies) finalSpecies.textContent = currentSpecies;
            if (finalLength) finalLength.textContent = `${data.length.toFixed(2)} cm`;
            if (resWeight) resWeight.textContent = `${Math.round(data.weight)} g`;
            if (resPhase) {
                resPhase.textContent = data.growth_phase;
            }

            // Reset loading state on button
            if (btnProceedWeight) {
                btnProceedWeight.disabled = false;
                btnProceedWeight.innerHTML = 'Proceed to Weight Calculation <i class="fa-solid fa-arrow-right" style="margin-left: 0.5rem;"></i>';
            }

            // Wizard Transition: Hide Loading, Show Step 2
            loadingState.classList.add('hidden');
            if (stepLength) stepLength.classList.remove('hidden');

        } catch (error) {
            alert(error.message);
            loadingState.classList.add('hidden');
            stepClassification.classList.remove('hidden');
            btnMeasure.disabled = false;
            btnMeasure.innerHTML = 'Proceed to Length Estimation <i class="fa-solid fa-arrow-right" style="margin-left: 0.5rem;"></i>';
        }
    });

    // Stage 3: Weight
    if (btnProceedWeight) {
        btnProceedWeight.addEventListener('click', () => {
            btnProceedWeight.disabled = true;
            btnProceedWeight.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Calculating Weight...';

            // Transition from stepLength to stepWeightPhase
            if (stepLength) stepLength.classList.add('hidden');
            loadingState.querySelector('h3').textContent = 'Estimating Weight & Phase...';
            loadingState.querySelector('p').textContent = 'Generating final report metrics';
            loadingState.classList.remove('hidden');

            setTimeout(() => {
                loadingState.classList.add('hidden');
                if (stepWeightPhase) stepWeightPhase.classList.remove('hidden');
            }, 1000);
        });
    }

});
