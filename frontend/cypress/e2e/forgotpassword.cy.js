/// <reference types="Cypress" />

describe("Forgot Password E2E", () => {
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
        cy.request({
          method: "GET",
          url: `${Cypress.env(
            "backend"
          )}/dev/delete-user?email=admin%40email.com`,
          body: { email: "admin@email.com" },
          form: true,
        });
        cy.visit("/forgot-password");
      });

      it("check for invalid email", () => {
        cy.contains("Forgot Password ?").should("be.visible");
        cy.get('[data-testid="emailInput"]').type("randomemail");
        cy.contains("Invalid Email").should("be.visible");
        cy.get('[data-testid="resetPasswordButton"]').should("be.disabled");
      });

      it("check for valid email (not registered email)", () => {
        cy.contains("Forgot Password ?").should("be.visible");
        cy.get('[data-testid="emailInput"]').type("admin123@email.com");
        cy.get('[data-testid="resetPasswordButton"]').should("not.be.disabled");
        cy.get('[data-testid="resetPasswordButton"]').click();
        cy.contains("Email not found").should("be.visible");
      });
    });
  });
});
