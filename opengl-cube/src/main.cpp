#include <GL/freeglut.h>
#include <iostream>

// Global variables for animation and camera
float rotationAngle = 0.0f;
float fov = 40.0f; // Initial FOV as requested

// Function to initialize OpenGL settings
void init() {
    glEnable(GL_DEPTH_TEST); // Enable depth buffering
    glClearColor(0.1f, 0.1f, 0.1f, 1.0f); // Dark grey background
}

// Function to draw the cube with different face colors
void drawCube() {
    glBegin(GL_QUADS);

    // Top face (Yellow)
    glColor3f(1.0f, 1.0f, 0.0f);
    glVertex3f(1.0f, 1.0f, -1.0f); glVertex3f(-1.0f, 1.0f, -1.0f);
    glVertex3f(-1.0f, 1.0f, 1.0f); glVertex3f(1.0f, 1.0f, 1.0f);

    // Bottom face (Magenta)
    glColor3f(1.0f, 0.0f, 1.0f);
    glVertex3f(1.0f, -1.0f, 1.0f); glVertex3f(-1.0f, -1.0f, 1.0f);
    glVertex3f(-1.0f, -1.0f, -1.0f); glVertex3f(1.0f, -1.0f, -1.0f);

    // Front face (Red)
    glColor3f(1.0f, 0.0f, 0.0f);
    glVertex3f(1.0f, 1.0f, 1.0f); glVertex3f(-1.0f, 1.0f, 1.0f);
    glVertex3f(-1.0f, -1.0f, 1.0f); glVertex3f(1.0f, -1.0f, 1.0f);

    // Back face (Cyan)
    glColor3f(0.0f, 1.0f, 1.0f);
    glVertex3f(1.0f, -1.0f, -1.0f); glVertex3f(-1.0f, -1.0f, -1.0f);
    glVertex3f(-1.0f, 1.0f, -1.0f); glVertex3f(1.0f, 1.0f, -1.0f);

    // Left face (Green)
    glColor3f(0.0f, 1.0f, 0.0f);
    glVertex3f(-1.0f, 1.0f, 1.0f); glVertex3f(-1.0f, 1.0f, -1.0f);
    glVertex3f(-1.0f, -1.0f, -1.0f); glVertex3f(-1.0f, -1.0f, 1.0f);

    // Right face (Blue)
    glColor3f(0.0f, 0.0f, 1.0f);
    glVertex3f(1.0f, 1.0f, -1.0f); glVertex3f(1.0f, 1.0f, 1.0f);
    glVertex3f(1.0f, -1.0f, 1.0f); glVertex3f(1.0f, -1.0f, -1.0f);

    glEnd();
}

void display() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glLoadIdentity();

    // Set camera: Position (10,10,10), LookAt (0,0,0), Up vector (0,1,0)
    gluLookAt(10.0, 10.0, 10.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0);

    // Continuous rotation around the Y-axis
    glRotatef(rotationAngle, 0.0f, 1.0f, 0.0f);

    drawCube();

    glutSwapBuffers();
}

void reshape(int w, int h) {
    if (h == 0) h = 1;
    float aspect = (float)w / (float)h;

    glViewport(0, 0, w, h);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    
    // Perspective projection using current FOV
    gluPerspective(fov, aspect, 1.0, 100.0);
    
    glMatrixMode(GL_MODELVIEW);
}

void update(int value) {
    rotationAngle += 1.5f; // Rotation speed
    if (rotationAngle > 360) rotationAngle -= 360;

    glutPostRedisplay();
    glutTimerFunc(16, update, 0); // ~60 FPS
}

// Handle Keyboard Zoom (+/-)
void keyboard(unsigned char key, int x, int y) {
    if (key == '+' || key == '=') fov -= 2.0f;
    if (key == '-' || key == '_') fov += 2.0f;

    // Clamp FOV to prevent inversion
    if (fov < 1.0f) fov = 1.0f;
    if (fov > 120.0f) fov = 120.0f;

    reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT));
}

// Handle Mouse Wheel Zoom (freeGLUT specific)
void mouseWheel(int wheel, int direction, int x, int y) {
    if (direction > 0) fov -= 2.0f; // Scroll up -> zoom in
    else fov += 2.0f;               // Scroll down -> zoom out

    if (fov < 1.0f) fov = 1.0f;
    if (fov > 120.0f) fov = 120.0f;

    reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT));
}

int main(int argc, char** argv) {
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(800, 600);
    glutCreateWindow("OpenGL Cube - Zoom with +/- or Scroll");

    init();

    glutDisplayFunc(display);
    glutReshapeFunc(reshape);
    glutKeyboardFunc(keyboard);
    glutMouseWheelFunc(mouseWheel); // freeGLUT feature
    glutTimerFunc(0, update, 0);

    glutMainLoop();
    return 0;
}