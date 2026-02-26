/* =====================================
   SECTION NAVIGATION (RADIO NAVBAR)
===================================== */

const navSteps = document.querySelectorAll(".nav-step");
const sections = document.querySelectorAll(".profile-section");

function activateSection(sectionId) {

    sections.forEach(sec => sec.classList.remove("active"));
    navSteps.forEach(btn => btn.classList.remove("active"));

    document.getElementById(sectionId).classList.add("active");

    document
        .querySelector(`.nav-step[data-section="${sectionId}"]`)
        .classList.add("active");
}

navSteps.forEach(btn => {
    btn.addEventListener("click", () => {
        activateSection(btn.dataset.section);
    });
});


/* =====================================
   EDIT MODE TOGGLE
===================================== */

const editBtn = document.getElementById("editBtn");
const saveBtn = document.getElementById("saveBtn");

editBtn.addEventListener("click", () => {

    document.querySelectorAll(".view-mode")
        .forEach(el => el.classList.add("hidden"));

    document.querySelectorAll(".edit-mode")
        .forEach(el => el.classList.remove("hidden"));

    editBtn.classList.add("hidden");
    saveBtn.classList.remove("hidden");
});


/* =====================================
   REMOVE ENTRY
===================================== */

document.addEventListener("click", function(e) {

    if (e.target.classList.contains("remove-entry")) {
        e.target.closest(".dynamic-entry").remove();
    }

});


/* =====================================
   ADD NEW ENTRY SYSTEM
===================================== */

document.querySelectorAll(".add-btn").forEach(btn => {

    btn.addEventListener("click", () => {

        const type = btn.dataset.type;

        if (type === "education") addEducation();
        if (type === "experience") addExperience();
        if (type === "project") addProject();
        if (type === "cert") addCertification();

    });

});


/* ---------- EDUCATION ---------- */

function addEducation() {

    const container = document.getElementById("educationContainer");

    container.insertAdjacentHTML("beforeend", `
        <div class="dynamic-entry editable-block">
            <div class="edit-mode">
                <input name="education_degree[]" placeholder="Degree">
                <input name="education_university[]" placeholder="University">
                <input name="education_year[]" placeholder="Year">
                <input name="education_grade[]" placeholder="Grade">
                <button type="button" class="remove-entry">Remove</button>
            </div>
        </div>
    `);
}


/* ---------- EXPERIENCE ---------- */

function addExperience() {

    const container = document.getElementById("experienceContainer");

    container.insertAdjacentHTML("beforeend", `
        <div class="dynamic-entry editable-block">
            <div class="edit-mode">
                <input name="experience_title[]" placeholder="Job Title">
                <input name="experience_company[]" placeholder="Company">
                <input name="experience_start[]" placeholder="Start Date">
                <input name="experience_end[]" placeholder="End Date">
                <button type="button" class="remove-entry">Remove</button>
            </div>
        </div>
    `);
}


/* ---------- PROJECT ---------- */

function addProject() {

    const container = document.getElementById("projectsContainer");

    container.insertAdjacentHTML("beforeend", `
        <div class="dynamic-entry editable-block">
            <div class="edit-mode">
                <input name="project_title[]" placeholder="Title">
                <input name="project_description[]" placeholder="Description">
                <input name="project_technologies[]" placeholder="Tech | separated">
                <button type="button" class="remove-entry">Remove</button>
            </div>
        </div>
    `);
}


/* ---------- CERTIFICATION ---------- */

function addCertification() {

    const container = document.getElementById("certContainer");

    container.insertAdjacentHTML("beforeend", `
        <div class="dynamic-entry editable-block">
            <div class="edit-mode">
                <input name="cert_name[]" placeholder="Certificate">
                <input name="cert_org[]" placeholder="Issuer">
                <button type="button" class="remove-entry">Remove</button>
            </div>
        </div>
    `);
}