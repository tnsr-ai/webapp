/// <reference types="Cypress" />

describe("Auth Login E2E", () => {
  const viewPorts = [{ width: 1920, height: 1080 }, "iphone-se2"];
  viewPorts.forEach((viewPort) => {
    const viewPortDescription =
      typeof viewPort === "object"
        ? `${viewPort.width}x${viewPort.height}`
        : viewPort;
    context(`Testing on ${viewPortDescription}`, () => {
      beforeEach(() => {
        if (typeof viewPort === "object") {
          cy.viewport(viewPort.width, viewPort.height);
        } else {
          cy.viewport(viewPort);
        }
        cy.visit("/");
      });

      it("check for email validation", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get("input[name=email]").type("testemail");
        cy.contains("Invalid Email").should("be.visible");
        cy.get("input[name=password]").type("testpassword");
        cy.get('[data-cy="signin-button"]').should("be.disabled");
      });

      it("check for password validation", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get("input[name=email]").type("admin@test.com");
        cy.get("input[name=password]").type("test");
        cy.get('[data-cy="signin-button"]').should("be.disabled");
      });

      it("check for valid credentials", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get("input[name=email]").type("test@email.com");
        cy.get("input[name=password]").type("testpassword");
        cy.get('[data-cy="signin-button"]').should("not.be.disabled");
      });

      it("check for incorrect credentials", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get("input[name=email]").type("test@email.com");
        cy.get("input[name=password]").type("testpassword");
        cy.get('[data-cy="signin-button"]').should("not.be.disabled");
        cy.get('[data-cy="signin-button"]').click();
        cy.contains("Invalid email or password").should("be.visible");
      });

      it("check for forgot password redirect", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get('[data-cy="forgot-password-link"]').click();
        cy.url().should("include", "/forgot-password");
      });

      it("check for signup redirect", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get('[data-cy="signup-link"]').click();
        cy.url().should("include", "/register");
      });

      it("check for login and redirect", () => {
        cy.contains("Sign In to tnsr.ai").should("be.visible");
        cy.get("input[name=email]").type("admin@tnsr.ai");
        cy.get("input[name=password]").type("password");
        cy.get('[data-cy="signin-button"]').should("not.be.disabled");
        cy.get('[data-cy="signin-button"]').click();
        cy.url().should("include", "/dashboard");
        cy.contains(
          "Please verify your email address to continue using the app."
        ).should("be.visible");
      });
    });
  });
});
