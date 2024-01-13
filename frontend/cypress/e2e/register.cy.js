/// <reference types="Cypress" />

describe("Register E2E", () => {
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
        cy.visit("/register");
        cy.request({
          method: "GET",
          url: `${Cypress.env(
            "backend"
          )}/dev/delete-user?email=admin%40email.com`,
          body: { email: "admin@email.com" },
          form: true,
        });
      });

      it("check for user form validation (incorrect)", () => {
        cy.contains("Create an Account").should("be.visible");
        cy.get('[data-testid="firstNameInput"]').type(" ");
        cy.get('[data-testid="lastNameInput"]').type(" ");
        cy.get('[data-testid="emailInput"]').type(" ");
        cy.get('[data-testid="passwordInput"]').type(" ");
        cy.get('[data-testid="confirmPasswordInput"]').type(" ");
        cy.get('[data-testid="signUpButton"]').should("be.disabled");
      });

      it("check for user form validation (correct)", () => {
        cy.contains("Create an Account").should("be.visible");
        cy.get('[data-testid="firstNameInput"]').type("fname");
        cy.get('[data-testid="lastNameInput"]').type("lname");
        cy.get('[data-testid="emailInput"]').type("admin@email.com");
        cy.get('[data-testid="passwordInput"]').type("password");
        cy.get('[data-testid="confirmPasswordInput"]').type("password");
        cy.get('[data-testid="signUpButton"]').should("not.be.disabled");
        cy.get('[data-testid="signUpButton"]').click();
        cy.url().should("include", "/dashboard");
        cy.contains(
          "Please verify your email address to continue using the app."
        ).should("be.visible");
      });

      it("check for user form validation (correct)", () => {
        cy.contains("Create an Account").should("be.visible");
        cy.get('[data-testid="firstNameInput"]').type("fname");
        cy.get('[data-testid="lastNameInput"]').type("lname");
        cy.get('[data-testid="emailInput"]').type("admin@email.com");
        cy.get('[data-testid="passwordInput"]').type("password");
        cy.get('[data-testid="confirmPasswordInput"]').type("password");
        cy.get('[data-testid="signUpButton"]').should("not.be.disabled");
        cy.get('[data-testid="signUpButton"]').click();
        cy.url().should("include", "/dashboard");
        cy.request({
          method: "GET",
          url: "http://localhost:8000/dev/verify-user?email=admin%40email.com",
          body: { email: "admin@email.com" },
          form: true,
        }).then((res) => {
          expect(res.status).to.eq(200);
        });
        cy.reload();
      });
    });
  });
});
