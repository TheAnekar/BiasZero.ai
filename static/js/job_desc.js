document.addEventListener("DOMContentLoaded", () => {
    const jobDescription = document.getElementById("job_description");
    const wordCount = document.getElementById("wordCount");
    const form = document.getElementById("jobForm");

    
    jobDescription.addEventListener("input", () => {
        const words = jobDescription.value.trim().split(/\s+/).filter(word => word.length > 0);
        wordCount.textContent = `Words: ${words.length}`;
    });

    
    form.addEventListener("submit", (e) => {
        const desc = jobDescription.value.trim();
        if (desc.length < 30) {
            e.preventDefault();
            alert("Please enter a more detailed job description (at least 30 characters).");
        }
    });
});
