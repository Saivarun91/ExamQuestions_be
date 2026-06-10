def _add_text(keys, key, value):
    if value is None:
        return
    text = str(value).strip()
    if text:
        keys[key] = text


def _add_faq_items(keys, prefix, faqs):
    for index, faq in enumerate(faqs or []):
        if not isinstance(faq, dict):
            continue
        _add_text(keys, f"{prefix}.faq.{index}.question", faq.get("question"))
        _add_text(keys, f"{prefix}.faq.{index}.answer", faq.get("answer"))


def _get_home_cms_keys():
    keys = {}

    try:
        from home.models import (
            HeroSection,
            SeoIntroSection,
            FAQsSection,
            BlogPostsSection,
            TestimonialsSection,
            TopCategoriesSection,
            ValuePropositionsSection,
            RecentlyUpdatedSection,
            EmailSubscribeSection,
            FeaturedExamsSection,
            PopularProvidersSection,
            SectionContent,
            ValueProposition,
            Testimonial,
            FAQ,
            CategoriesPageSeo,
            ExamsPageSeo,
            ProvidersPageSeo,
            HomePageSeo,
        )

        hero = HeroSection.objects.first()
        if hero:
            _add_text(keys, "cms.hero.title", hero.title)
            _add_text(keys, "cms.hero.subtitle", hero.subtitle)
            if hero.stats:
                for index, stat in enumerate(hero.stats[:6]):
                    label = (stat or {}).get("label")
                    _add_text(keys, f"cms.hero.stat{index + 1}.label", label)

        seo = SeoIntroSection.objects.first()
        if seo:
            _add_text(keys, "cms.seo.heading", seo.heading)
            _add_text(keys, "cms.seo.content", seo.content)

        sections = [
            (TopCategoriesSection, "cms.categories.heading", "heading"),
            (TopCategoriesSection, "cms.categories.subtitle", "subtitle"),
            (FeaturedExamsSection, "cms.featured.heading", "heading"),
            (FeaturedExamsSection, "cms.featured.subtitle", "subtitle"),
            (ValuePropositionsSection, "cms.value.heading", "heading"),
            (ValuePropositionsSection, "cms.value.subtitle", "subtitle"),
            (BlogPostsSection, "cms.blog.heading", "heading"),
            (BlogPostsSection, "cms.blog.subtitle", "subtitle"),
            (TestimonialsSection, "cms.testimonials.heading", "heading"),
            (TestimonialsSection, "cms.testimonials.subtitle", "subtitle"),
            (FAQsSection, "cms.faq.heading", "heading"),
            (FAQsSection, "cms.faq.subtitle", "subtitle"),
            (RecentlyUpdatedSection, "cms.recent.heading", "heading"),
            (RecentlyUpdatedSection, "cms.recent.subtitle", "subtitle"),
            (PopularProvidersSection, "cms.providers.heading", "heading"),
            (PopularProvidersSection, "cms.providers.subtitle", "subtitle"),
            (EmailSubscribeSection, "cms.subscribe.title", "title"),
            (EmailSubscribeSection, "cms.subscribe.subtitle", "subtitle"),
        ]

        for model, key, field in sections:
            doc = model.objects.first()
            if doc:
                _add_text(keys, key, getattr(doc, field, None))

        section_content = SectionContent.objects.first()
        if section_content:
            _add_text(keys, "cms.faq.section.heading", section_content.heading)
            _add_text(keys, "cms.faq.section.content", section_content.content)

        for item in ValueProposition.objects.filter(is_active=True):
            item_id = str(item.id)
            _add_text(keys, f"cms.value.{item_id}.title", item.title)
            _add_text(keys, f"cms.value.{item_id}.description", item.description)

        for item in Testimonial.objects.filter(is_active=True):
            item_id = str(item.id)
            _add_text(keys, f"cms.testimonial.{item_id}.text", item.text)
            _add_text(keys, f"cms.testimonial.{item_id}.role", item.role)

        for faq in FAQ.objects.filter(is_active=True):
            faq_id = str(faq.id)
            _add_text(keys, f"cms.faq.{faq_id}.question", faq.question)
            _add_text(keys, f"cms.faq.{faq_id}.answer", faq.answer)

        page_seo_models = [
            (
                CategoriesPageSeo,
                "categories_page",
                ["meta_title", "meta_description", "hero_title", "hero_subtitle"],
            ),
            (
                ExamsPageSeo,
                "exams_page",
                ["meta_title", "meta_description", "page_h1"],
            ),
            (
                ProvidersPageSeo,
                "providers_page",
                ["meta_title", "meta_description"],
            ),
            (HomePageSeo, "home_page", ["meta_title", "meta_description"]),
        ]

        for model, prefix, fields in page_seo_models:
            doc = model.objects(is_active=True).first() or model.objects.first()
            if not doc:
                continue
            for field in fields:
                _add_text(keys, f"cms.{prefix}.{field}", getattr(doc, field, None))

    except Exception:
        pass

    return keys


def _get_category_keys():
    keys = {}

    try:
        from categories.models import Category

        for category in Category.objects():
            category_id = str(category.id)
            prefix = f"cms.category.{category_id}"
            _add_text(keys, f"{prefix}.title", category.title)
            _add_text(keys, f"{prefix}.description", category.description)
            _add_text(keys, f"{prefix}.content", category.content)
            _add_text(keys, f"{prefix}.hero_title", category.hero_title)
            _add_text(keys, f"{prefix}.hero_subtitle", category.hero_subtitle)
            _add_text(keys, f"{prefix}.meta_title", category.meta_title)
            _add_text(keys, f"{prefix}.meta_description", category.meta_description)
            _add_faq_items(keys, prefix, category.faqs)
    except Exception:
        pass

    return keys


def _get_provider_keys():
    keys = {}

    try:
        from providers.models import Provider

        for provider in Provider.objects():
            provider_id = str(provider.id)
            prefix = f"cms.provider.{provider_id}"
            _add_text(keys, f"{prefix}.name", provider.name)
            _add_text(keys, f"{prefix}.page_title", provider.page_title)
            _add_text(keys, f"{prefix}.content", provider.content)
            _add_text(keys, f"{prefix}.meta_title", provider.meta_title)
            _add_text(keys, f"{prefix}.meta_description", provider.meta_description)
            _add_faq_items(keys, prefix, provider.faqs)
    except Exception:
        pass

    return keys


def _get_course_keys():
    keys = {}

    try:
        from courses.models import Course

        course_fields = [
            "title",
            "short_description",
            "about",
            "eligibility",
            "exam_pattern",
            "why_matters",
            "hero_title",
            "hero_subtitle",
            "test_description",
            "meta_title",
            "meta_description",
            "official_details_content",
            "official_details_page_title",
        ]

        for course in Course.objects():
            course_id = str(course.id)
            prefix = f"cms.course.{course_id}"

            for field in course_fields:
                _add_text(keys, f"{prefix}.{field}", getattr(course, field, None))

            for index, topic in enumerate(course.topics or []):
                if isinstance(topic, dict):
                    _add_text(
                        keys,
                        f"{prefix}.topic.{index}.name",
                        topic.get("name") or topic.get("title"),
                    )

            for index, item in enumerate(course.whats_included or []):
                _add_text(keys, f"{prefix}.included.{index}", item)

            for index, item in enumerate(course.testimonials or []):
                if isinstance(item, dict):
                    _add_text(keys, f"{prefix}.testimonial.{index}.text", item.get("text"))
                    _add_text(keys, f"{prefix}.testimonial.{index}.name", item.get("name"))

            _add_faq_items(keys, prefix, course.faqs)

            for index, plan in enumerate(course.pricing_plans or []):
                if not isinstance(plan, dict):
                    continue
                _add_text(keys, f"{prefix}.pricing_plan.{index}.name", plan.get("name"))
                _add_text(keys, f"{prefix}.pricing_plan.{index}.description", plan.get("description"))

            _add_faq_items(keys, f"{prefix}.pricing", course.pricing_faqs)
    except Exception:
        pass

    return keys


def _get_blog_keys():
    keys = {}

    try:
        from blog.models import Blog

        for blog in Blog.objects():
            blog_id = str(blog.id)
            prefix = f"cms.blog.{blog_id}"
            _add_text(keys, f"{prefix}.title", blog.title)
            _add_text(keys, f"{prefix}.excerpt", blog.excerpt)
            _add_text(keys, f"{prefix}.meta_title", blog.meta_title)
            _add_text(keys, f"{prefix}.meta_description", blog.meta_description)
    except Exception:
        pass

    return keys


def get_cms_translation_keys():
    keys = {}
    keys.update(_get_home_cms_keys())
    keys.update(_get_category_keys())
    keys.update(_get_provider_keys())
    keys.update(_get_course_keys())
    keys.update(_get_blog_keys())
    return keys
