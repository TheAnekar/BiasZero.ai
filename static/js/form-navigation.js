
(function() {
    'use strict';

    
    let currentStep = 1;
    const totalSteps = 7;

    
    const formSteps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.step');
    const progressBar = document.getElementById('progressBar');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const form = document.getElementById('resumeForm');
    const successOverlay = document.getElementById('successOverlay');

   
    function init() {
        updateUI();
        attachEventListeners();
    }

    
    function attachEventListeners() {
        nextBtn.addEventListener('click', handleNext);
        prevBtn.addEventListener('click', handlePrev);
        form.addEventListener('submit', handleSubmit);
    }

   
    function handleNext() {
        if (validateCurrentStep()) {
            if (currentStep < totalSteps) {
                currentStep++;
                updateUI();
                
                
                if (currentStep === 7) {
                    populateReview();
                }
            }
        }
    }

    function handlePrev() {
        if (currentStep > 1) {
            currentStep--;
            updateUI();
        }
    }

    
    function handleSubmit(e) {
        e.preventDefault();
        
        
        const termsAccept = document.getElementById('termsAccept');
        if (!termsAccept.checked) {
            alert('Please confirm that all information is accurate');
            return;
        }
        
        
        const formData = new FormData(form);
        
      
        showSuccess();
    }

    function showSuccess() {
        successOverlay.classList.add('show');
        
        
        setTimeout(() => {
            successOverlay.classList.remove('show');
            resetForm();
        }, 3000);
    }

    
    function updateUI() {
        updateSteps();
        updateProgressBar();
        updateButtons();
        scrollToTop();
    }

    function updateSteps() {
        
        formSteps.forEach((step, index) => {
            step.classList.remove('active');
            if (index === currentStep - 1) {
                step.classList.add('active');
            }
        });

        
        progressSteps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            const stepNum = index + 1;
            
            if (stepNum === currentStep) {
                step.classList.add('active');
            } else if (stepNum < currentStep) {
                step.classList.add('completed');
            }
        });
    }

    function updateProgressBar() {
        const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
        progressBar.style.width = progress + '%';
    }

    function updateButtons() {
        
        prevBtn.style.display = currentStep === 1 ? 'none' : 'block';
        
        
        if (currentStep === totalSteps) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'block';
        } else {
            nextBtn.style.display = 'block';
            submitBtn.style.display = 'none';
        }
    }

    function scrollToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    
    function validateCurrentStep() {
        const currentFormStep = document.querySelector(`.form-step[data-step="${currentStep}"]`);
        const inputs = currentFormStep.querySelectorAll('input[required], select[required], textarea[required]');
        
        let isValid = true;
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            alert('Please fill in all required fields correctly before proceeding.');
        }
        
        return isValid;
    }

    function validateField(field) {
        if (field.required) {
            
            const parentSection = field.closest('.dynamic-section');
            if (parentSection && parentSection.style.display === 'none') {
                return true; 
            }
            
            if (field.type === 'checkbox') {
                return field.checked;
            } else if (field.value.trim() === '') {
                field.style.borderColor = '#ef4444';
                return false;
            }
        }
        
        field.style.borderColor = '';
        return true;
    }

    
    function populateReview() {
        const reviewContent = document.getElementById('reviewContent');
        let html = '';

        
        html += '<div class="review-section">';
        html += '<h3>Personal Information</h3>';
        html += createReviewItem('Name', document.getElementById('name').value);
        html += createReviewItem('Age', document.getElementById('age').value);
        html += createReviewItem('Gender', getGenderLabel(document.getElementById('gender').value));
        html += createReviewItem('Location', document.getElementById('location').value);
        html += createReviewItem('Email', document.getElementById('email').value);
        html += createReviewItem('Phone', document.getElementById('phone').value);
        html += '</div>';

        
        if (document.getElementById('hasEducation').checked) {
            html += '<div class="review-section">';
            html += '<h3>Education</h3>';
            const eduDegrees = document.getElementsByName('education_degree[]');
            const eduUniversities = document.getElementsByName('education_university[]');
            const eduYears = document.getElementsByName('education_year[]');
            const eduGrades = document.getElementsByName('education_grade[]');
            
            for (let i = 0; i < eduDegrees.length; i++) {
                if (eduDegrees[i].value) {
                    html += `<div style="margin-bottom: 1rem; padding: 1rem; background: var(--background); border-radius: 8px;">`;
                    html += `<strong>Education ${i + 1}</strong><br>`;
                    html += `${eduDegrees[i].value}<br>`;
                    html += `${eduUniversities[i].value} (${eduYears[i].value})<br>`;
                    html += `Grade: ${eduGrades[i].value}`;
                    html += `</div>`;
                }
            }
            html += '</div>';
        }

       
        if (document.getElementById('hasExperience').checked) {
            html += '<div class="review-section">';
            html += '<h3>Work Experience</h3>';
            const expTitles = document.getElementsByName('experience_title[]');
            const expCompanies = document.getElementsByName('experience_company[]');
            const expStarts = document.getElementsByName('experience_start[]');
            const expEnds = document.getElementsByName('experience_end[]');
            
            for (let i = 0; i < expTitles.length; i++) {
                if (expTitles[i].value) {
                    html += `<div style="margin-bottom: 1rem; padding: 1rem; background: var(--background); border-radius: 8px;">`;
                    html += `<strong>${expTitles[i].value}</strong><br>`;
                    html += `${expCompanies[i].value}<br>`;
                    html += `${expStarts[i].value} - ${expEnds[i].value}`;
                    html += `</div>`;
                }
            }
            html += '</div>';
        }

        
        if (document.getElementById('hasProjects').checked) {
            html += '<div class="review-section">';
            html += '<h3>Projects</h3>';
            const projTitles = document.getElementsByName('project_title[]');
            const projDescriptions = document.getElementsByName('project_description[]');
            const projTechnologies = document.getElementsByName('project_technologies[]');
            
            for (let i = 0; i < projTitles.length; i++) {
                if (projTitles[i].value) {
                    html += `<div style="margin-bottom: 1rem; padding: 1rem; background: var(--background); border-radius: 8px;">`;
                    html += `<strong>${projTitles[i].value}</strong><br>`;
                    html += `${projDescriptions[i].value}<br>`;
                    html += `<em>Technologies: ${projTechnologies[i].value}</em>`;
                    html += `</div>`;
                }
            }
            html += '</div>';
        }

        
        if (document.getElementById('hasCertifications').checked) {
            html += '<div class="review-section">';
            html += '<h3>Certifications</h3>';
            const certNames = document.getElementsByName('cert_name[]');
            const certOrgs = document.getElementsByName('cert_org[]');
            
            for (let i = 0; i < certNames.length; i++) {
                if (certNames[i].value) {
                    html += `<div style="margin-bottom: 1rem; padding: 1rem; background: var(--background); border-radius: 8px;">`;
                    html += `<strong>${certNames[i].value}</strong><br>`;
                    html += `${certOrgs[i].value}`;
                    html += `</div>`;
                }
            }
            html += '</div>';
        }

        
        if (document.getElementById('hasSkills').checked) {
            html += '<div class="review-section">';
            html += '<h3>Skills</h3>';
            const techSkills = document.getElementById('technical_skills').value;
            const softSkills = document.getElementById('soft_skills').value;
            
            if (techSkills) {
                html += createReviewItem('Technical Skills', techSkills);
            }
            if (softSkills) {
                html += createReviewItem('Soft Skills', softSkills);
            }
            html += '</div>';
        }

        reviewContent.innerHTML = html;
    }

    function createReviewItem(label, value) {
        return `
            <div class="review-item">
                <span class="review-label">${label}:</span>
                <span class="review-value">${value || '-'}</span>
            </div>
        `;
    }

    function getGenderLabel(value) {
        const labels = { 'm': 'Male', 'f': 'Female', 'o': 'Other' };
        return labels[value] || value;
    }

    
    function resetForm() {
        form.reset();
        currentStep = 1;
        updateUI();
        
        
        document.getElementById('educationEntries').innerHTML = '';
        document.getElementById('experienceEntries').innerHTML = '';
        document.getElementById('projectEntries').innerHTML = '';
        document.getElementById('certificationEntries').innerHTML = '';
        
        
        document.getElementById('technicalTags').innerHTML = '';
        document.getElementById('softTags').innerHTML = '';
        document.getElementById('technical_skills').value = '';
        document.getElementById('soft_skills').value = '';
    }

    
    document.addEventListener('DOMContentLoaded', init);

})();