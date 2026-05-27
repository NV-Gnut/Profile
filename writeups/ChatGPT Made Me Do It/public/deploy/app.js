const express = require('express');
const session = require('express-session');
const cookieParser = require('cookie-parser');

const { PORT, SESSION_SECRET } = require('./config');
const { csrfProtection } = require('./middleware');
const routes = require('./routes');

const app = express();

app.use(express.urlencoded({ extended: false }));
app.use(express.static('public'));
app.use(cookieParser());
app.use(
  session({
    name: 'connect.sid',
    secret: SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      path: '/',
      sameSite: 'strict',
    },
  }),
);

app.use(csrfProtection);
app.use('/', routes);

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
