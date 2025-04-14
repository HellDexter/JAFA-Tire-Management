/* JAFA Tire Management - Main JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // Aktivace Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Aktivace popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Dynamické načítání pozic pneumatik pro vozidla
    const vehicleSelect = document.getElementById('vehicle_id');
    const positionSelect = document.getElementById('position_id');
    
    if (vehicleSelect && positionSelect) {
        vehicleSelect.addEventListener('change', function() {
            const vehicleId = this.value;
            if (vehicleId) {
                // Vyčištění aktuálních možností
                positionSelect.innerHTML = '<option value="">Vyberte pozici...</option>';
                positionSelect.disabled = true;
                
                // Načtení pozic pro vybrané vozidlo
                fetch(`/api/positions/${vehicleId}`)
                    .then(response => response.json())
                    .then(data => {
                        positionSelect.disabled = false;
                        
                        data.forEach(position => {
                            if (!position.tire_mounted) {
                                const option = document.createElement('option');
                                option.value = position.id;
                                option.textContent = `${position.code} - ${position.description}`;
                                positionSelect.appendChild(option);
                            }
                        });
                        
                        if (positionSelect.options.length <= 1) {
                            const option = document.createElement('option');
                            option.textContent = 'Žádné volné pozice';
                            option.disabled = true;
                            positionSelect.appendChild(option);
                        }
                    })
                    .catch(error => {
                        console.error('Chyba při načítání pozic:', error);
                    });
            }
        });
    }
    
    // Aktualizace nájezdu vozidla při montáži/demontáži
    const vehicleSelectForMileage = document.querySelector('select[name="vehicle_id"]');
    const mileageInput = document.querySelector('input[name="mileage"]');
    
    if (vehicleSelectForMileage && mileageInput) {
        vehicleSelectForMileage.addEventListener('change', function() {
            const vehicleId = this.value;
            if (vehicleId) {
                const selectedOption = this.options[this.selectedIndex];
                const currentMileage = selectedOption.getAttribute('data-mileage');
                if (currentMileage) {
                    mileageInput.value = currentMileage;
                }
            }
        });
    }
    
    // Přidání podpory nahrávání více fotek v demontážním formuláři
    const photoInputs = document.querySelectorAll('.multi-photo-upload');
    
    photoInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileList = this.files;
            const previewContainer = document.getElementById('photo-previews');
            
            if (previewContainer) {
                previewContainer.innerHTML = '';
                
                for (let i = 0; i < fileList.length; i++) {
                    const file = fileList[i];
                    
                    if (file.type.match('image.*')) {
                        const reader = new FileReader();
                        
                        reader.onload = function(e) {
                            const preview = document.createElement('div');
                            preview.className = 'col-md-3 mb-3';
                            preview.innerHTML = `
                                <div class="card">
                                    <img src="${e.target.result}" class="card-img-top" alt="Náhled fotky">
                                    <div class="card-body p-2">
                                        <p class="card-text small text-muted">${file.name}</p>
                                    </div>
                                </div>
                            `;
                            previewContainer.appendChild(preview);
                        };
                        
                        reader.readAsDataURL(file);
                    }
                }
            }
        });
    });
    
    // Aktualizace grafu na stránce reportů, pokud existuje
    const lifeSpanChart = document.getElementById('lifespan-chart');
    if (lifeSpanChart) {
        const ctx = lifeSpanChart.getContext('2d');
        const chartData = JSON.parse(lifeSpanChart.getAttribute('data-chart'));
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Průměrný nájezd (km)',
                    data: chartData.data,
                    backgroundColor: 'rgba(0, 123, 255, 0.5)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Kilometrů'
                        }
                    }
                }
            }
        });
    }
    
    // Dynamické vyhledávání a filtrování v tabulkách
    const tableFilter = document.getElementById('table-filter');
    const dataTable = document.getElementById('data-table');
    
    if (tableFilter && dataTable) {
        tableFilter.addEventListener('keyup', function() {
            const filterText = this.value.toLowerCase();
            const rows = dataTable.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(filterText)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Konfirmační dialogy pro mazání položek
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Opravdu chcete smazat tuto položku? Tato akce je nevratná.')) {
                e.preventDefault();
            }
        });
    });
    
    // Automatické generování reportů
    const generateReportBtn = document.getElementById('generate-report-btn');
    
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', function() {
            const reportType = document.getElementById('report-type').value;
            const fromDate = document.getElementById('from-date').value;
            const toDate = document.getElementById('to-date').value;
            
            window.location.href = `/reports/generate?type=${reportType}&from=${fromDate}&to=${toDate}`;
        });
    }
    
    // Živý výpočet procentuálního opotřebení pneumatiky
    const initialDepthInput = document.getElementById('initial_tread_depth');
    const currentDepthInput = document.getElementById('current_tread_depth');
    const wearPercentageDisplay = document.getElementById('wear-percentage');
    
    if (initialDepthInput && currentDepthInput && wearPercentageDisplay) {
        function updateWearPercentage() {
            const initialDepth = parseFloat(initialDepthInput.value) || 0;
            const currentDepth = parseFloat(currentDepthInput.value) || 0;
            
            if (initialDepth > 0) {
                const wearPercentage = ((initialDepth - currentDepth) / initialDepth * 100).toFixed(1);
                wearPercentageDisplay.textContent = `${wearPercentage}%`;
                
                // Vizuální indikátor
                if (wearPercentage > 75) {
                    wearPercentageDisplay.className = 'badge bg-danger';
                } else if (wearPercentage > 50) {
                    wearPercentageDisplay.className = 'badge bg-warning text-dark';
                } else {
                    wearPercentageDisplay.className = 'badge bg-success';
                }
            } else {
                wearPercentageDisplay.textContent = 'N/A';
                wearPercentageDisplay.className = 'badge bg-secondary';
            }
        }
        
        initialDepthInput.addEventListener('input', updateWearPercentage);
        currentDepthInput.addEventListener('input', updateWearPercentage);
        
        // Inicializace
        updateWearPercentage();
    }
});
