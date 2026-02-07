
(function() {
    'use strict';

    
    let educationCount = 1;
    let experienceCount = 1;
    let projectCount = 1;
    let certificationCount = 1;

    
    function initToggles() {
        const toggles = [
            { checkbox: 'hasEducation', section: 'educationSection' },
            { checkbox: 'hasExperience', section: 'experienceSection' },
            { checkbox: 'hasProjects', section: 'projectsSection' },
            { checkbox: 'hasCertifications', section: 'certificationsSection' },
            { checkbox: 'hasSkills', section: 'skillsSection' }
        ];

        toggles.forEach(({ checkbox, section }) => {
            const checkboxEl = document.getElementById(checkbox);
            const sectionEl = document.getElementById(section);
            
            if (checkboxEl && sectionEl) {
                checkboxEl.addEventListener('change', function() {
                    sectionEl.style.display = this.checked ? 'block' : 'none';
                   
                    updateRequiredFields(sectionEl, this.checked);
                });
            }
        });
    }

    
    function updateRequiredFields(section, isRequired) {
        const inputs = section.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.hasAttribute('data-originally-required') || input.required) {
                input.setAttribute('data-originally-required', 'true');
                input.required = isRequired;
            }
        });
    }

    
    window.addEducationEntry = function() {
        educationCount++;
        const container = document.getElementById('educationEntries');
        const newEntry = document.createElement('div');
        newEntry.className = 'dynamic-entry';
        newEntry.setAttribute('data-entry-type', 'education');
        newEntry.innerHTML = `
            <div class="entry-header">
                <h3 class="entry-title">Education #${educationCount}</h3>
                <button type="button" class="btn-remove" onclick="removeEntry(this)">Remove</button>
            </div>
            
            <div class="form-group">
                <label>Degree *</label>
                <input type="text" name="education_degree[]" placeholder="e.g., Bachelor's in Computer Science" required>
            </div>
            
            <div class="form-group">
                <label>University/Institution *</label>
                <input type="text" name="education_university[]" placeholder="e.g., MIT" required>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Year of Completion *</label>
                    <input type="number" name="education_year[]" min="1950" max="2030" placeholder="2020" required>
                </div>
                
                <div class="form-group">
                    <label>Grade/Percentage *</label>
                    <input type="number" step="0.01" name="education_grade[]" placeholder="8.5 or 85%" required>
                </div>
            </div>
        `;
        container.appendChild(newEntry);
        updateRemoveButtons('education');
    };

    
    window.addExperienceEntry = function() {
        experienceCount++;
        const container = document.getElementById('experienceEntries');
        const newEntry = document.createElement('div');
        newEntry.className = 'dynamic-entry';
        newEntry.setAttribute('data-entry-type', 'experience');
        newEntry.innerHTML = `
            <div class="entry-header">
                <h3 class="entry-title">Experience #${experienceCount}</h3>
                <button type="button" class="btn-remove" onclick="removeEntry(this)">Remove</button>
            </div>
            
            <div class="form-group">
                <label>Job Title *</label>
                <input type="text" name="experience_title[]" placeholder="e.g., Software Engineer" required>
            </div>
            
            <div class="form-group">
                <label>Company *</label>
                <input type="text" name="experience_company[]" placeholder="e.g., Google Inc." required>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Start Date (MM/YYYY) *</label>
                    <input type="text" name="experience_start[]" placeholder="08/2020" pattern="(0[1-9]|1[0-2])\\/\\d{4}" required>
                    <small class="form-hint">Format: MM/YYYY</small>
                </div>
                
                <div class="form-group">
                    <label>End Date (MM/YYYY) *</label>
                    <input type="text" name="experience_end[]" placeholder="03/2023 or Present" required>
                    <small class="form-hint">Format: MM/YYYY or "Present"</small>
                </div>
            </div>
        `;
        container.appendChild(newEntry);
        updateRemoveButtons('experience');
    };

    
    window.addProjectEntry = function() {
        projectCount++;
        const container = document.getElementById('projectEntries');
        const newEntry = document.createElement('div');
        newEntry.className = 'dynamic-entry';
        newEntry.setAttribute('data-entry-type', 'project');
        newEntry.innerHTML = `
            <div class="entry-header">
                <h3 class="entry-title">Project #${projectCount}</h3>
                <button type="button" class="btn-remove" onclick="removeEntry(this)">Remove</button>
            </div>
            
            <div class="form-group">
                <label>Project Title *</label>
                <input type="text" name="project_title[]" placeholder="e.g., E-commerce Platform" required>
            </div>
            
            <div class="form-group">
                <label>Description *</label>
                <textarea name="project_description[]" rows="4" placeholder="Describe your project, its purpose, and impact..." required></textarea>
            </div>
            
            <div class="form-group">
                <label>Technologies Used *</label>
                <input type="text" name="project_technologies[]" placeholder="React, Node.js, MongoDB (separate with |)" required>
                <small class="form-hint">Separate technologies with | (pipe symbol)</small>
            </div>
        `;
        container.appendChild(newEntry);
        updateRemoveButtons('project');
    };

    
    window.addCertificationEntry = function() {
        certificationCount++;
        const container = document.getElementById('certificationEntries');
        const newEntry = document.createElement('div');
        newEntry.className = 'dynamic-entry';
        newEntry.setAttribute('data-entry-type', 'certification');
        newEntry.innerHTML = `
            <div class="entry-header">
                <h3 class="entry-title">Certification #${certificationCount}</h3>
                <button type="button" class="btn-remove" onclick="removeEntry(this)">Remove</button>
            </div>
            
            <div class="form-group">
                <label>Certification Name *</label>
                <input type="text" name="cert_name[]" placeholder="e.g., AWS Certified Developer">
            </div>
            
            <div class="form-group">
                <label>Issuing Organization *</label>
                <input type="text" name="cert_org[]" placeholder="e.g., Amazon Web Services">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Issue Date</label>
                    <input type="month" name="cert_issue[]">
                </div>
                
                <div class="form-group">
                    <label>Expiry Date (if applicable)</label>
                    <input type="month" name="cert_expiry[]">
                </div>
            </div>
        `;
        container.appendChild(newEntry);
        updateRemoveButtons('certification');
    };

   
    window.removeEntry = function(button) {
        const entry = button.closest('.dynamic-entry');
        const entryType = entry.getAttribute('data-entry-type');
        entry.remove();
        
        
        renumberEntries(entryType);
        updateRemoveButtons(entryType);
    };

    
    function renumberEntries(type) {
        const container = document.getElementById(`${type}Entries`);
        const entries = container.querySelectorAll('.dynamic-entry');
        entries.forEach((entry, index) => {
            const title = entry.querySelector('.entry-title');
            const typeName = type.charAt(0).toUpperCase() + type.slice(1);
            title.textContent = `${typeName} #${index + 1}`;
        });
        
        
        if (type === 'education') educationCount = entries.length;
        else if (type === 'experience') experienceCount = entries.length;
        else if (type === 'project') projectCount = entries.length;
        else if (type === 'certification') certificationCount = entries.length;
    }

    
    function updateRemoveButtons(type) {
        const container = document.getElementById(`${type}Entries`);
        const entries = container.querySelectorAll('.dynamic-entry');
        const removeButtons = container.querySelectorAll('.btn-remove');
        
        
        removeButtons.forEach((btn, index) => {
            btn.style.display = entries.length > 1 ? 'block' : 'none';
        });
    }

    
    function initTagInput(inputId, tagsContainerId, hiddenInputId) {
        const input = document.getElementById(inputId);
        const tagsContainer = document.getElementById(tagsContainerId);
        const hiddenInput = document.getElementById(hiddenInputId);
        const tags = [];

        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const value = this.value.trim();
                
                if (value && !tags.includes(value)) {
                    tags.push(value);
                    addTag(value, tagsContainer, tags, hiddenInput);
                    this.value = '';
                }
            }
        });
    }

   
    function addTag(text, container, tagsArray, hiddenInput) {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            <span>${text}</span>
            <button type="button" class="tag-remove" onclick="removeTag(this, '${text}', '${hiddenInput.id}')">×</button>
        `;
        container.appendChild(tag);
        updateHiddenInput(tagsArray, hiddenInput);
    }

    
    window.removeTag = function(button, tagText, hiddenInputId) {
        const tag = button.closest('.tag');
        const hiddenInput = document.getElementById(hiddenInputId);
        
        
        const tagsContainer = tag.parentElement;
        const inputId = hiddenInputId === 'technical_skills' ? 'technicalSkillInput' : 'softSkillInput';
        const input = document.getElementById(inputId);
        
       
        const currentTags = hiddenInput.value ? hiddenInput.value.split(',') : [];
        const index = currentTags.indexOf(tagText);
        
        if (index > -1) {
            currentTags.splice(index, 1);
            hiddenInput.value = currentTags.join(',');
        }
        
        tag.remove();
    };

    
    function updateHiddenInput(tagsArray, hiddenInput) {
        hiddenInput.value = tagsArray.join(',');
    }

    
    document.addEventListener('DOMContentLoaded', function() {
        initToggles();
        initTagInput('technicalSkillInput', 'technicalTags', 'technical_skills');
        initTagInput('softSkillInput', 'softTags', 'soft_skills');
    });

})();