// Home: the phone on the right shows the screen of the last section whose top has passed the middle of the window.
// Beside it, one dot per screen: the current one is marked, and a click scrolls to that screen's section.
(() => {
  const preview = document.querySelector(".preview");
  const shots = [...document.querySelectorAll(".preview img[data-screen]")];
  const sections = [...document.querySelectorAll("section[data-screen]")];
  if (!preview || !shots.length || !sections.length) return;

  // The dots, labelled with each screenshot's description.
  const nav = document.createElement("nav");
  nav.className = "screens";
  nav.setAttribute("aria-label", document.documentElement.lang === "fr" ? "Écrans" : "Screens");
  const dots = shots.map((img) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.screen = img.dataset.screen;
    button.setAttribute("aria-label", img.alt);
    button.title = img.alt;
    button.addEventListener("click", () => {
      const target = sections.find((s) => s.dataset.screen === img.dataset.screen);
      const smooth = !matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (target === sections[0]) scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" });
      else target.scrollIntoView({ block: "center", behavior: smooth ? "smooth" : "auto" });
    });
    nav.append(button);
    return button;
  });
  preview.append(nav);

  let current = null;
  const update = () => {
    const middle = innerHeight / 2;
    let name = sections[0].dataset.screen;
    for (const s of sections) if (s.getBoundingClientRect().top <= middle) name = s.dataset.screen;
    if (name === current) return;
    current = name;
    shots.forEach((img) => img.classList.toggle("is-active", img.dataset.screen === name));
    dots.forEach((dot) => dot.setAttribute("aria-current", String(dot.dataset.screen === name)));
  };

  let queued = false;
  const onScroll = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; update(); });
  };
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);
  update();
})();
