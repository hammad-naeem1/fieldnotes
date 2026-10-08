---
title: "Contact me"
description: "Get in touch with Hammad Naeem about internships, projects, or machine learning."
permalink: /contact/
---
<section class="listing-hero wrap contact-hero">
  <a class="back-link" href="{{ '/' | relative_url }}">← Home</a>
  <p class="eyebrow">CONTACT ME <span>/</span> LET’S CONNECT</p>
  <h1>Have a question<br>or an opportunity?</h1>
  <p class="article-deck">I’m happy to hear about internships, project collaborations, machine learning, or useful feedback on something I’ve shared.</p>
</section>
<section class="wrap contact-content">
  <div class="contact-primary">
    <div><p class="eyebrow">THE BEST WAY TO REACH ME</p><h2>Send me an email.</h2><p>Include a little context about what you’re reaching out about, and I’ll know where to start.</p></div>
    <a class="button button-dark" href="mailto:{{ site.contact_email }}">{{ site.contact_email }} <span aria-hidden="true">↗</span></a>
  </div>
  <div class="contact-grid">
    <a class="contact-link-card" href="{{ site.github_url }}" target="_blank" rel="noopener noreferrer"><span class="course-label">CODE AND PROJECTS</span><strong>GitHub</strong><span>See my repositories and project work ↗</span></a>
    <a class="contact-link-card" href="{{ site.huggingface_url }}" target="_blank" rel="noopener noreferrer"><span class="course-label">MODELS AND DEMOS</span><strong>Hugging Face</strong><span>Open my profile: {{ site.huggingface_username }} ↗</span></a>
    <div class="contact-link-card contact-discord"><span class="course-label">COMMUNITY</span><strong>Discord</strong><span>Username: <code>{{ site.discord_username }}</code><br>Send me a server invite if you want this to be a clickable link.</span></div>
  </div>
  <p class="contact-footnote">This is a static website, so it does not collect or store messages in a contact form. The email button opens your email app.</p>
</section>
